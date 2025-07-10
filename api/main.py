import asyncio
import logging
import uvicorn
import click
import sys
import re

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

from contextlib import asynccontextmanager
from pathlib import Path

from core.models import *

from config.app_constants import app_constants
from config.security import security_config
from config.settings import settings

from services.spotify_playlist_service import spotify_playlist_service
from services.playlist_draft_service import playlist_draft_service
from services.playlist_generator import playlist_generator_service
from services.prompt_validator import prompt_validator_service
from services.personality_service import personality_service
from services.rate_limiter import rate_limiter_service
from services.database_service import db_service
from services.data_service import data_loader
from services.ai_service import ai_service

from utils.decorators import *

from endpoints import *

class CustomFormatter(logging.Formatter):
    def format(self, record):
        raw_level = record.levelname
        color = app_constants.LOGGER_COLORS.get(raw_level, None)

        colored_level = click.style(raw_level, fg=color) if color else raw_level

        target_width = 10
        level_label_len = len(raw_level) + 1
        spaces = " " * max(0, target_width - level_label_len)

        record.levelname = f"{colored_level}:{spaces}"

        return super().format(record)

handler = logging.StreamHandler()
formatter = CustomFormatter('%(levelname)s%(message)s')
handler.setFormatter(formatter)

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    handlers=[handler]
)

logger = logging.getLogger(__name__)

api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""

    logger.info(f"Starting {app_constants.API_NAME} API...")
    config_errors = settings.validate_required_settings()

    if config_errors:
        logger.error("Configuration validation failed:")

        for error in config_errors:
            logger.error(f"  - {error}")

        if not settings.DEBUG:
            raise Exception("Production configuration validation failed")

        else:
            logger.warning("Running in DEBUG mode with configuration issues")

    try:
        await db_service.initialize()

        init_tasks = [
            rate_limiter_service.initialize(),
            ai_service.initialize(),
            prompt_validator_service.initialize(),
            playlist_generator_service.initialize(),
            playlist_draft_service.initialize(),
            spotify_playlist_service.initialize(),
            personality_service.initialize()
        ]

        cache_task = asyncio.create_task(preload_data_cache())
        await asyncio.gather(*init_tasks)

        logger.info(f"AI Service: {'ENABLED' if ai_service else 'DISABLED'}")
        logger.info(f"Rate Limiting: {'ENABLED' if settings.PLAYLIST_LIMIT_ENABLED else 'DISABLED'}")

    except Exception as e:
        logger.error(f"Failed to initialize {app_constants.API_NAME} API: {e}")
        raise

    yield

async def preload_data_cache():
    """Pre-load frequently used data in background"""

    try:
        loop = asyncio.get_event_loop()

        preload_tasks = [
            loop.run_in_executor(None, data_loader.get_mood_patterns),
            loop.run_in_executor(None, data_loader.get_genre_patterns),
            loop.run_in_executor(None, data_loader.get_activity_patterns),
            loop.run_in_executor(None, data_loader.get_energy_trigger_words),
        ]

        await asyncio.gather(*preload_tasks, return_exceptions=True)
        logger.info("Data cache preloaded successfully")

    except Exception as e:
        logger.warning(f"Cache preloading failed (non-critical): {e}")

app = FastAPI(
    title=app_constants.API_TITLE,
    description="AI-powered playlist generation with real-time song search",
    version=app_constants.API_VERSION,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="templates"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    nonce = None

    if hasattr(response, 'body') and b'nonce=' in response.body:
        body_str = response.body.decode('utf-8')
        nonce_match = re.search(r'nonce="([^"]+)"', body_str)

        if nonce_match:
            nonce = nonce_match.group(1)

    headers = security_config.get_security_headers(nonce)

    for header, value in headers.items():
        response.headers[header] = value

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,
)

@app.get("/")
async def root_endpoint():
    return await root()

@app.post("/auth/init", response_model=AuthInitResponse)
async def auth_init_endpoint(request: AuthInitRequest):
    """Initialize Spotify OAuth flow"""

    return await auth_init(request)

@app.get("/auth/callback")
async def auth_callback_endpoint(code: str = None, state: str = None, error: str = None):
    """Handle Spotify OAuth callback"""

    return await auth_callback(code, state, error)

@app.post("/auth/validate", response_model=SessionValidationResponse)
async def validate_session_endpoint(request: SessionValidationRequest):
    """Validate session"""

    return await validate_session(request)

@app.get("/auth/check-session")
async def check_session_endpoint(request: Request):
    """Check if a session exists for the given device ID"""

    return await check_session(request)

@app.post("/auth/rate-limit-status", response_model=RateLimitStatus)
async def get_authenticated_rate_limit_status_endpoint(request: SessionValidationRequest):
    """Get current rate limit status for the authenticated user"""

    return await get_authenticated_rate_limit_status(request)


@app.post("/auth/register-device", response_model=DeviceRegistrationResponse)
async def register_device_endpoint(request: DeviceRegistrationRequest):
    """Register a new device"""

    return await register_device(request)

@app.post("/auth/demo-playlist-refinements")
async def get_demo_playlist_refinements_endpoint(request: DemoPlaylistRefinementsRequest):
    """Get refinement count for a specific demo playlist"""

    return await get_demo_playlist_refinements(request)

@app.post("/auth/logout")
async def logout_endpoint(request: Request):
    """Logout and completely clear all device data"""

    return await logout(request)

@app.post("/auth/cleanup")
@debug_only
async def cleanup_sessions_endpoint():
    """Clean up expired sessions and auth attempts"""

    return await cleanup_sessions()

@app.post("/auth/account-type")
async def get_account_type_endpoint(request: SessionValidationRequest):
    """Get account type for a session"""

    return await get_account_type(request)

@app.get("/config")
@debug_only
async def get_config_endpoint():
    """Get client configuration values"""

    return await get_config()

@app.get("/config/health")
async def health_check_endpoint():
    """Check API health and service status"""

    return await health_check()

@app.post("/config/reload")
@debug_only
async def reload_config_endpoint():
    """Reload JSON configuration files without restarting the server"""

    return await reload_config()

@app.post("/playlist/generate", response_model=PlaylistResponse)
async def generate_playlist_endpoint(request: PlaylistRequest):
    """Generate a playlist using AI-powered real-time song search"""

    return await generate_playlist(request)

@app.post("/playlist/refine", response_model=PlaylistResponse)
async def refine_playlist_endpoint(request: PlaylistRequest):
    """Refine an existing playlist based on user feedback"""

    return await refine_playlist(request)

@app.post("/playlist/update-draft", response_model=PlaylistResponse)
async def update_playlist_draft_endpoint(request: PlaylistRequest):
    """Update an existing playlist draft without AI refinement (no refinement count increase)"""

    return await update_playlist_draft(request)

@app.post("/playlist/library", response_model=LibraryPlaylistsResponse)
async def get_library_playlists_endpoint(request: LibraryPlaylistsRequest):
    """Get user's Spotify playlists."""

    return await get_library_playlists(request)

@app.post("/playlist/drafts")
async def get_draft_playlist_endpoint(request: PlaylistDraftRequest):
    """Get a specific draft playlist."""

    return await get_draft_playlist(request)

@app.delete("/playlist/drafts")
async def delete_draft_playlist_endpoint(request: PlaylistDraftRequest):
    """Delete a draft playlist."""

    return await delete_draft_playlist(request)

@app.post("/spotify/create-playlist", response_model=SpotifyPlaylistResponse)
async def create_spotify_playlist_endpoint(request: SpotifyPlaylistRequest):
    """Create a Spotify playlist from a draft."""

    return await create_spotify_playlist(request)

@app.post("/spotify/playlist/tracks")
async def get_spotify_playlist_tracks_endpoint(request: SpotifyPlaylistTracksRequest):
    """Get tracks from a Spotify playlist."""

    return await get_spotify_playlist_tracks(request)

@app.delete("/spotify/playlist")
async def delete_spotify_playlist_endpoint(request: SpotifyPlaylistDeleteRequest):
    """Delete/unfollow a Spotify playlist."""

    return await delete_spotify_playlist(request)

@app.post("/personality/save", response_model=UserPersonalityResponse)
async def save_user_personality_endpoint(request: UserPersonalityRequest):
    """Save user personality preferences"""
    return await save_user_personality(request)

@app.get("/personality/load")
async def load_user_personality_endpoint(request: Request):
    """Load user personality preferences"""

    return await load_user_personality(request)

@app.post("/personality/clear")
async def clear_user_personality_endpoint(request: UserPersonalityClearRequest):
    """Clear user personality preferences"""

    return await clear_user_personality(request)

@app.get("/user/followed-artists", response_model=FollowedArtistsResponse)
async def get_followed_artists_endpoint(request: Request, limit: int = 50):
    """Get user's followed artists from Spotify"""

    return await get_followed_artists(request, limit)

@app.post("/user/search-artists", response_model=ArtistSearchResponse)
async def search_artists_endpoint(request: ArtistSearchRequest):
    """Search for artists on Spotify"""

    return await search_artists(request)

@app.delete("/spotify/playlist/track")
async def remove_track_from_spotify_playlist_endpoint(request: SpotifyPlaylistTrackRemoveRequest):
    """Remove a track from a Spotify playlist."""

    return await remove_track_from_spotify_playlist(request)
    
@app.get("/ai/models")
@debug_only
async def get_ai_models_endpoint():
    """Get available AI models and their configurations"""

    return await get_ai_models()

@app.post("/ai/test")
@debug_only
async def test_ai_model_endpoint(request: Request):
    """Test AI model with a simple prompt"""

    return await test_ai_model(request)

@app.get("/config/production-check")
@debug_only
async def production_readiness_check_endpoint():
    """Check if the API is ready for production deployment"""

    return await production_readiness_check()

@app.get("/server/mode")
async def get_server_mode_endpoint():
    """Get current server mode"""

    return await get_server_mode()

if __name__ == "__main__":
    logger.info(app_constants.STARTUP_MESSAGE)

    uvicorn.run(
        "main:app",

        host=settings.API_HOST,
        port=settings.API_PORT,

        log_level=settings.LOG_LEVEL.lower(),

        reload=settings.DEBUG,
        reload_dirs=[f"{api_dir}/config", f"{api_dir}/core", f"{api_dir}/services"],
        reload_excludes=["__pycache__"]
    )
