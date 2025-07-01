import asyncio
import logging
import uvicorn
import click
import sys
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from contextlib import asynccontextmanager
from pathlib import Path

from core.models import *

from config.app_constants import AppConstants
from config.settings import settings

from services.spotify_playlist_service import spotify_playlist_service
from services.playlist_draft_service import playlist_draft_service
from services.playlist_generator import playlist_generator_service
from services.prompt_validator import prompt_validator_service
from services.personality_service import personality_service
from services.security import validate_production_readiness
from services.template_service import template_service
from services.rate_limiter import rate_limiter_service
from services.auth_middleware import AuthMiddleware
from services.security import get_security_headers
from services.database_service import db_service
from services.auth_service import auth_service
from config.ai_models import ai_model_manager
from services.data_loader import data_loader
from services.ai_service import ai_service
from services.security import debug_only

class CustomFormatter(logging.Formatter):
    def format(self, record):
        raw_level = record.levelname
        color = AppConstants.LOGGER_COLORS.get(raw_level, None)

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

auth_middleware = AuthMiddleware(auth_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""

    logger.info(f"Starting {AppConstants.APP_NAME} API...")
    
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
        logger.info(f"Spotify Search: {'ENABLED' if playlist_generator_service.spotify_search.is_ready() else 'DISABLED'}")
        logger.info(f"Rate Limiting: {'ENABLED' if settings.PLAYLIST_LIMIT_ENABLED else 'DISABLED'}")
        logger.info(f"Auth Service: {'ENABLED' if auth_service.is_ready() else 'DISABLED'}")
        logger.info(f"Playlist Drafts: {'ENABLED' if playlist_draft_service.is_ready() else 'DISABLED'}")
        logger.info(f"Spotify Playlists: {'ENABLED' if spotify_playlist_service.is_ready() else 'DISABLED'}")

    except Exception as e:
        logger.error(f"Failed to initialize {AppConstants.APP_NAME} API: {e}")
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
    title=AppConstants.API_TITLE,
    description="AI-powered playlist generation with real-time song search",
    version=AppConstants.API_VERSION,
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""

    response = await call_next(request)
    headers = get_security_headers()
    
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

def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input to prevent injection attacks"""

    if not text:
        return ""

    text = text[:max_length]
    text = re.sub(r'\s+', ' ', text).strip()
    dangerous_chars = ['<script', '</script', '<iframe', '</iframe', 'javascript:', 'vbscript:', 'onload=', 'onclick=']

    for dangerous in dangerous_chars:
        text = text.replace(dangerous, '')
    
    return text

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)

    if settings.SECURE_HEADERS:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"

    return response

@app.get("/")
async def root():
    return {
        "message": AppConstants.API_WELCOME_MESSAGE,
        "description": "AI-powered playlist generation with real-time song search",
        "endpoints": {
            "generate": "/generate-playlist",
            "refine": "/refine-playlist",
            "update_draft": "/update-playlist-draft",
            "health": "/health",
            "rate_limit": "/rate-limit-status/{device_id}",
            "auth_init": "/auth/init",
            "auth_callback": "/auth/callback",
            "auth_validate": "/auth/validate",
            "library": "/library/playlists",
            "add_to_spotify": "/spotify/create-playlist",
            "get_draft": "/drafts/{playlist_id}"
        }
    }

@app.post("/auth/init", response_model=AuthInitResponse)
async def auth_init(request: AuthInitRequest):
    """Initialize Spotify OAuth flow"""

    try:
        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")

        if not await auth_service.validate_device(request.device_id, update_last_seen=False):
            try:
                await auth_service.register_device_with_id(
                    device_id=request.device_id,
                    platform=request.platform
                )

            except Exception as e:
                logger.error(f"Failed to auto-register device: {e}")
                raise HTTPException(status_code=500, detail="Failed to register device")

        auth_url, state = auth_service.generate_auth_url(request.device_id, request.platform)

        await auth_service.store_auth_state(state, request.device_id, request.platform)
        return AuthInitResponse(auth_url=auth_url, state=state)

    except Exception as e:
        logger.error(f"Auth init failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize authentication")

@app.get("/auth/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle Spotify OAuth callback"""

    try:
        if error:
            logger.warning(f"OAuth error: {error}")
            html_content = template_service.render_template("auth_error.html", error=error)

            return HTMLResponse(content=html_content)

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing authorization code or state")

        session_id = await auth_service.handle_spotify_callback(code, state)

        if not session_id:
            raise HTTPException(status_code=400, detail="Failed to create session")

        html_content = template_service.render_template("auth_success.html", session_id=session_id)
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Auth callback failed: {e}")
        html_content = template_service.render_template("auth_error.html")

        return HTMLResponse(content=html_content)

@app.post("/auth/validate", response_model=SessionValidationResponse)
async def validate_session(request: SessionValidationRequest):
    """Validate session"""

    try:
        is_valid = await auth_service.validate_session(request.session_id, request.device_id)
        return SessionValidationResponse(valid=is_valid)

    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        raise HTTPException(status_code=500, detail="Session validation failed")

@app.get("/auth/check-session/{device_id}")
async def check_session(device_id: str):
    """Check if a session exists for the given device ID (for desktop polling)"""

    try:
        session_id = await auth_service.get_session_by_device(device_id)

        if session_id:
            return {"session_id": session_id}

        else:
            return {"session_id": None}

    except Exception as e:
        logger.error(f"Check session failed: {e}")
        return {"session_id": None}

async def require_auth(request: PlaylistRequest):
    if not settings.AUTH_REQUIRED:
        return None

    if not await auth_service.validate_device(request.device_id):
        raise HTTPException(status_code=403, detail="Invalid device ID. Please register device first.")

    if not hasattr(request, 'session_id') or not request.session_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        return user_info

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/health")
async def health_check():
    """Check API health and service status"""

    if settings.DEBUG:
        return {
            "status": "healthy",
            "version": AppConstants.API_VERSION, 
            "services": {
                "prompt_validator": prompt_validator_service.is_ready(),
                "playlist_generator": playlist_generator_service.is_ready(),
                "rate_limiter": rate_limiter_service.is_ready()
            },
            "features": {
                "spotify_search": playlist_generator_service.spotify_search.is_ready(),
                "ai_generation": True,  # AI generation is always available when configured
                "rate_limiting": settings.PLAYLIST_LIMIT_ENABLED
            }
        }

    else:
        logger.warning("API health check is disabled in production mode")
        raise HTTPException(status_code=403, detail="API health check is disabled in production mode")

@app.get("/config")
async def get_config():
    """Get client configuration values"""
    return {
        "personality": {
            "max_favorite_artists": settings.MAX_FAVORITE_ARTISTS,
            "max_disliked_artists": settings.MAX_DISLIKED_ARTISTS,
            "max_favorite_genres": settings.MAX_FAVORITE_GENRES,
            "max_preferred_decades": settings.MAX_PREFERRED_DECADES,
        },
        "playlists": {
            "max_songs_per_playlist": settings.MAX_SONGS_PER_PLAYLIST,
            "max_playlists_per_day": settings.MAX_PLAYLISTS_PER_DAY,
            "max_refinements_per_playlist": settings.MAX_REFINEMENTS_PER_PLAYLIST,
        },
        "features": {
            "auth_required": settings.AUTH_REQUIRED,
            "playlist_limit_enabled": settings.PLAYLIST_LIMIT_ENABLED,
            "refinement_limit_enabled": settings.REFINEMENT_LIMIT_ENABLED,
        }
    }

@app.post("/reload-config")
@debug_only
async def reload_config():
    """Reload JSON configuration files without restarting the server (Debug mode only)"""
    try:
        data_loader.reload_cache()
        logger.info("Configuration files reloaded successfully")

        return {
            "message": "Configuration reloaded successfully",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")

@app.post("/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(request: PlaylistRequest):
    """Generate a playlist using AI-powered real-time song search"""

    try:
        sanitized_prompt = sanitize_user_input(request.prompt, max_length=500)

        if not sanitized_prompt:
            raise HTTPException(status_code=400, detail="Invalid or empty prompt")
        
        user_info = await require_auth(request)
        rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id

        if settings.PLAYLIST_LIMIT_ENABLED and not await rate_limiter_service.can_make_request(rate_limit_key):
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit of {settings.MAX_PLAYLISTS_PER_DAY} playlists reached. Try again tomorrow."
            )

        is_valid_prompt = await prompt_validator_service.validate_prompt(sanitized_prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The prompt doesn't seem to be related to music or mood. Please try a different description."
            )

        user_context = request.user_context

        if not user_context and request.session_id:
            try:
                user_context = await personality_service.get_user_personality(
                    session_id=request.session_id,
                    device_id=request.device_id
                )

            except Exception as e:
                logger.warning(f"Failed to load user personality: {e}")

        if user_context and request.session_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists(
                    session_id=request.session_id,
                    device_id=request.device_id,
                    user_context=user_context
                )

                user_context.favorite_artists = merged_artists

            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.generate_playlist(
            prompt=sanitized_prompt,
            user_context=user_context,
            count=request.count if settings.DEBUG else settings.MAX_SONGS_PER_PLAYLIST,
            discovery_strategy=request.discovery_strategy or "balanced"
        )

        playlist_id = await playlist_draft_service.save_draft(
            device_id=request.device_id,
            session_id=request.session_id,
            prompt=sanitized_prompt,
            songs=songs,
            refinements_used=0
        )

        if settings.PLAYLIST_LIMIT_ENABLED:
            await rate_limiter_service.record_request(rate_limit_key)

        return PlaylistResponse(
            songs=songs,
            generated_from=sanitized_prompt,
            total_count=len(songs),
            is_refinement=False,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating playlist: {str(e)}")

@app.post("/refine-playlist", response_model=PlaylistResponse)
async def refine_playlist(request: PlaylistRequest):
    """Refine an existing playlist based on user feedback"""

    try:
        user_info = await require_auth(request)
        rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id
        current_songs = request.current_songs or []
        refinements_used = 0
        playlist_id = request.playlist_id

        if playlist_id:
            draft = await playlist_draft_service.get_draft(playlist_id)

            if draft:
                current_songs = draft.songs
                refinements_used = draft.refinements_used

                if settings.REFINEMENT_LIMIT_ENABLED and refinements_used >= settings.MAX_REFINEMENTS_PER_PLAYLIST:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Maximum of {settings.MAX_REFINEMENTS_PER_PLAYLIST} AI refinements reached for this playlist."
                    )

            else:
                logger.warning(f"Draft playlist {playlist_id} not found, using provided songs")

        else:
            if settings.REFINEMENT_LIMIT_ENABLED and not await rate_limiter_service.can_refine_playlist(rate_limit_key):
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum daily refinements reached."
                )

        is_valid_prompt = await prompt_validator_service.validate_prompt(request.prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The refinement request doesn't seem to be music-related. Please try a different description."
            )

        user_context = request.user_context

        if not user_context and request.session_id:
            try:
                user_context = await personality_service.get_user_personality(
                    session_id=request.session_id,
                    device_id=request.device_id
                )

            except Exception as e:
                logger.warning(f"Failed to load user personality: {e}")

        if user_context and request.session_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists(
                    session_id=request.session_id,
                    device_id=request.device_id,
                    user_context=user_context
                )

                user_context.favorite_artists = merged_artists

            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.refine_playlist(
            original_songs=current_songs,
            refinement_prompt=request.prompt,
            user_context=user_context,
            count=request.count or 30,
            discovery_strategy=request.discovery_strategy or "balanced"
        )

        if playlist_id:
            await playlist_draft_service.update_draft(
                playlist_id=playlist_id,
                songs=songs,
                refinements_used=refinements_used + 1
            )

        else:
            playlist_id = await playlist_draft_service.save_draft(
                device_id=request.device_id,
                session_id=request.session_id,
                prompt=f"Refined: {request.prompt}",
                songs=songs,
                refinements_used=1
            )

        if settings.REFINEMENT_LIMIT_ENABLED:
            await rate_limiter_service.record_refinement(rate_limit_key)

        return PlaylistResponse(
            songs=songs,
            generated_from=request.prompt,
            total_count=len(songs),
            is_refinement=True,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining playlist: {str(e)}")

@app.post("/update-playlist-draft", response_model=PlaylistResponse)
async def update_playlist_draft(request: PlaylistRequest):
    """Update an existing playlist draft without AI refinement (no refinement count increase)"""
    
    try:
        user_info = await require_auth(request)
        playlist_id = request.playlist_id
        current_songs = request.current_songs or []
        
        if not playlist_id:
            raise HTTPException(status_code=400, detail="Playlist ID is required for updates")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        success = await playlist_draft_service.update_draft(
            playlist_id=playlist_id,
            songs=current_songs,
            refinements_used=draft.refinements_used,
            prompt=request.prompt or draft.prompt
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update draft playlist")

        return PlaylistResponse(
            songs=current_songs,
            generated_from=request.prompt or draft.prompt,
            total_count=len(current_songs),
            is_refinement=False,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating playlist draft: {str(e)}")

@app.get("/rate-limit-status/{device_id}", response_model=RateLimitStatus)
async def get_rate_limit_status(device_id: str):
    """Get current rate limit status for a device (legacy endpoint - insecure)"""

    logger.warning(f"Using insecure rate limit endpoint for device: {device_id}")

    try:
        return await rate_limiter_service.get_status(device_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {str(e)}")

@app.post("/auth/rate-limit-status", response_model=RateLimitStatus)
async def get_authenticated_rate_limit_status(request: SessionValidationRequest):
    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        rate_limit_key = user_info["spotify_user_id"]

        return await rate_limiter_service.get_status(rate_limit_key)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Rate limit status error: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {str(e)}")

@app.post("/auth/register-device", response_model=DeviceRegistrationResponse)
async def register_device(request: DeviceRegistrationRequest):
    """Register a new device and get server-generated UUID"""

    try:
        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")

        device_id, registration_timestamp = await auth_service.register_device(
            platform=request.platform,
            app_version=request.app_version,
            device_fingerprint=request.device_fingerprint
        )

        return DeviceRegistrationResponse(
            device_id=device_id,
            registration_timestamp=registration_timestamp
        )

    except Exception as e:
        logger.error(f"Device registration failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to register device")

@app.post("/spotify/create-playlist", response_model=SpotifyPlaylistResponse)
async def create_spotify_playlist(request: SpotifyPlaylistRequest):
    """Create a Spotify playlist from a draft."""

    try:
        user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        draft = await playlist_draft_service.get_draft(request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.session_id and draft.session_id != request.session_id:
            draft_user_info = await auth_service.get_user_from_session(draft.session_id)
            current_user_spotify_id = user_info.get('spotify_user_id')
            draft_user_spotify_id = draft_user_info.get('spotify_user_id') if draft_user_info else None

            logger.info(f"Cross-device check: draft user {draft_user_spotify_id}, current user {current_user_spotify_id}")
            logger.info(f"Draft user info: {draft_user_info}")
            logger.info(f"Current user info: {user_info}")

            if current_user_spotify_id != draft_user_spotify_id:
                logger.warning(f"Access denied: draft belongs to user {draft_user_spotify_id}, current user is {current_user_spotify_id}")
                raise HTTPException(status_code=403, detail="This draft belongs to a different user")

        elif not draft.session_id and draft.device_id != request.device_id:
            logger.warning(f"Access denied: draft device {draft.device_id}, current device {request.device_id}")
            raise HTTPException(status_code=403, detail="This draft belongs to a different device")

        access_token = await auth_service.get_access_token(request.session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

        spotify_playlist_id, playlist_url = await spotify_playlist_service.create_playlist(
            access_token=access_token,
            name=request.name,
            songs=draft.songs,
            description=request.description,
            public=request.public or False
        )

        await playlist_draft_service.mark_as_added_to_spotify(
            playlist_id=request.playlist_id,
            spotify_playlist_id=spotify_playlist_id,
            spotify_url=playlist_url,
            user_id=user_info.get('spotify_user_id'),
            device_id=request.device_id,
            session_id=request.session_id,
            playlist_name=request.name
        )

        logger.info(f"Created Spotify playlist {spotify_playlist_id} from draft {request.playlist_id}")

        return SpotifyPlaylistResponse(
            success=True,
            spotify_playlist_id=spotify_playlist_id,
            playlist_url=playlist_url,
            message="Playlist created successfully"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to create Spotify playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Spotify playlist")

@app.post("/library/playlists", response_model=LibraryPlaylistsResponse)
async def get_library_playlists(request: LibraryPlaylistsRequest):
    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        spotify_user_id = user_info.get("spotify_user_id")
        drafts = []

        try:
            drafts = await playlist_draft_service.get_user_drafts(
                user_id=spotify_user_id,
                device_id=request.device_id,
                session_id=request.session_id,
                include_spotify=False
            )

        except Exception as e:
            logger.warning(f"Failed to get user drafts for {spotify_user_id}: {e}")

        if not drafts:
            logger.info(f"No user-based drafts found for {spotify_user_id}, falling back to device drafts")

            try:
                drafts = await playlist_draft_service.get_device_drafts(
                    device_id=request.device_id,
                    include_spotify=False
                )

            except Exception as e:
                logger.error(f"Failed to get device drafts: {e}")
                drafts = []

        spotify_playlists = []

        if spotify_playlist_service.is_ready():
            try:
                access_token = await auth_service.get_access_token(request.session_id)

                if access_token:
                    echotuner_playlist_ids = await playlist_draft_service.get_user_echotuner_spotify_playlist_ids(
                        user_info.get('spotify_user_id')
                    )

                    if echotuner_playlist_ids:
                        all_playlists = await spotify_playlist_service.get_user_playlists(access_token)
                        spotify_playlists = []

                        for playlist in all_playlists:
                            if playlist.get('id') in echotuner_playlist_ids:
                                try:
                                    playlist_details = await spotify_playlist_service.get_playlist_details(
                                        access_token, playlist['id']
                                    )

                                    tracks_count = playlist_details.get('tracks', {}).get('total', 0)

                                except Exception as e:
                                    logger.warning(f"Failed to get fresh track count for playlist {playlist['id']}: {e}")
                                    tracks_count = playlist.get('tracks', {}).get('total', 0)

                                spotify_playlist_info = SpotifyPlaylistInfo(
                                    id=playlist['id'],
                                    name=playlist.get('name', 'Unknown'),
                                    description=playlist.get('description'),
                                    tracks_count=tracks_count,
                                    refinements_used=0,
                                    max_refinements=0,
                                    can_refine=False,
                                    spotify_url=playlist.get('external_urls', {}).get('spotify'),
                                    images=playlist.get('images', [])
                                )

                                spotify_playlists.append(spotify_playlist_info)

            except Exception as e:
                logger.warning(f"Failed to fetch Spotify playlists: {e}")

        return LibraryPlaylistsResponse(
            drafts=drafts,
            spotify_playlists=spotify_playlists
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get library playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to get library playlists")

@app.get("/drafts/{playlist_id}")
async def get_draft_playlist(playlist_id: str, device_id: str = None):
    """Get a specific draft playlist."""

    try:
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id parameter required")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return draft

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get draft playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get draft playlist")

@app.delete("/drafts/{playlist_id}")
async def delete_draft_playlist(playlist_id: str, device_id: str = None):
    """Delete a draft playlist."""

    try:
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id parameter required")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if draft.status != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft playlists")

        success = await playlist_draft_service.delete_draft(playlist_id)

        if success:
            return {"message": "Draft playlist deleted successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete draft playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

@app.get("/spotify/playlist/{playlist_id}/tracks")
async def get_spotify_playlist_tracks(playlist_id: str, session_id: str = None, device_id: str = None):
    """Get tracks from a Spotify playlist."""

    try:
        if not session_id or not device_id:
            raise HTTPException(status_code=400, detail="session_id and device_id parameters required")

        user_info = await auth_service.validate_session_and_get_user(session_id, device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        access_token = await auth_service.get_access_token(session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

        tracks = await spotify_playlist_service.get_playlist_tracks(access_token, playlist_id)

        return {"tracks": tracks}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get Spotify playlist tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Spotify playlist tracks")

@app.delete("/spotify/playlist/{playlist_id}")
async def delete_spotify_playlist(playlist_id: str, session_id: str = None, device_id: str = None):
    """Delete/unfollow a Spotify playlist."""

    try:
        if not session_id or not device_id:
            raise HTTPException(status_code=400, detail="session_id and device_id parameters required")

        user_info = await auth_service.validate_session_and_get_user(session_id, device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        access_token = await auth_service.get_access_token(session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

        success = await spotify_playlist_service.delete_playlist(access_token, playlist_id)
        
        if success:
            await playlist_draft_service.remove_spotify_playlist_tracking(playlist_id)
            return {"message": "Playlist deleted/unfollowed successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete playlist from Spotify")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete Spotify playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Spotify playlist")

@app.post("/personality/save", response_model=UserPersonalityResponse)
async def save_user_personality(request: UserPersonalityRequest):
    """Save user personality preferences"""

    try:
        logger.info(f"Saving personality for session {request.session_id}")

        success = await personality_service.save_user_personality(
            session_id=request.session_id,
            device_id=request.device_id,
            user_context=request.user_context
        )

        if success:
            logger.info("Personality saved successfully")
            return UserPersonalityResponse(success=True, message="Personality saved successfully")

        else:
            logger.error("Personality save failed")
            raise HTTPException(status_code=500, detail="Failed to save personality")

    except Exception as e:
        logger.error(f"Failed to save user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to save personality")

@app.get("/personality/load")
async def load_user_personality(request: Request):
    try:
        user_info = await auth_middleware.validate_session_from_headers(request)
        
        session_id = request.headers.get('session-id')
        device_id = request.headers.get('device-id')

        user_context = await personality_service.get_user_personality(
            session_id=session_id,
            device_id=device_id
        )

        if user_context:
            return {"user_context": user_context.model_dump()}
        else:
            return {"user_context": None}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to load user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to load personality")

@app.post("/personality/clear")
async def clear_user_personality(request: UserPersonalityClearRequest):
    """Clear user personality preferences"""

    try:
        user_info = await auth_service.get_user_from_session(request.session_id)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid session")

        spotify_user_id = user_info.get('spotify_user_id')

        success = await db_service.execute_query(
            "DELETE FROM user_personalities WHERE user_id = ?",
            (spotify_user_id,)
        )

        return {"success": True, "message": "Personality cleared successfully"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to clear user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear personality")

@app.get("/user/followed-artists", response_model=FollowedArtistsResponse)
async def get_followed_artists(request: Request, limit: int = 50):
    """Get user's followed artists from Spotify"""

    try:
        session_id = request.headers.get('session-id')
        device_id = request.headers.get('device-id')

        if not session_id or not device_id:
            raise HTTPException(status_code=422, detail="Missing session-id or device-id headers")

        artists = await personality_service.get_followed_artists(
            session_id=session_id,
            device_id=device_id,
            limit=limit
        )

        return FollowedArtistsResponse(artists=artists)

    except Exception as e:
        logger.warning(f"Failed to get followed artists: {e}")
        return FollowedArtistsResponse(artists=[])

@app.post("/user/search-artists", response_model=ArtistSearchResponse)
async def search_artists(request: ArtistSearchRequest):
    """Search for artists on Spotify"""

    try:
        artists = await personality_service.search_artists(
            session_id=request.session_id,
            device_id=request.device_id,
            query=request.query,
            limit=request.limit or 20
        )

        return ArtistSearchResponse(artists=artists)

    except Exception as e:
        logger.error(f"Failed to search artists: {e}")
        raise HTTPException(status_code=500, detail="Failed to search artists")

@app.delete("/spotify/playlist/{playlist_id}/track")
async def remove_track_from_spotify_playlist(playlist_id: str, track_uri: str, session_id: str = None, device_id: str = None):
    """Remove a track from a Spotify playlist."""

    try:
        if not spotify_playlist_service._initialized:
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        access_token = await auth_service.get_access_token(session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

        success = await spotify_playlist_service.remove_track_from_playlist(access_token, playlist_id, track_uri)

        if success:
            return {"message": "Track removed successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to remove track from Spotify")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to remove track from Spotify playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove track from playlist")
    
@app.get("/ai/models")
@debug_only
async def get_ai_models():
    """Get available AI models and their configurations (Debug mode only)."""

    models = {}

    for model_id in ai_service.list_available_models():
        try:
            model_info = ai_service.get_model_info(model_id)
            models[model_id] = model_info

        except Exception as e:
            models[model_id] = {"error": str(e)}
    
    return {
        "available_models": models,
        "default_model": ai_model_manager.get_default_model()
    }

@app.post("/ai/test")
@debug_only
async def test_ai_model(request: Request):
    """Test AI model with a simple prompt (Debug mode only)."""

    try:
        data = await request.json()
        model_id = data.get("model_id")
        prompt = data.get("prompt", "Hello, this is a test.")
        response = await ai_service.generate_text(prompt, model_id=model_id)

        return {
            "success": True,
            "model_used": ai_service.get_model_info(model_id),
            "response": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI test failed: {str(e)}")

@app.get("/production-check")
@debug_only
async def production_readiness_check():
    """Check if the API is ready for production deployment (Debug mode only)."""

    issues = validate_production_readiness()

    return {
        "production_ready": len(issues) == 0,
        "issues": issues,
        "recommendations": [
            "Set DEBUG=false in production",
            "Enable AUTH_REQUIRED=true",
            "Enable SECURE_HEADERS=true",
            "Configure rate limiting",
            "Use HTTPS in production",
            "Set up proper logging",
            "Configure monitoring"
        ]
    }

if __name__ == "__main__":
    logger.info(AppConstants.STARTUP_MESSAGE)

    uvicorn.run(
        "main:app",

        host=settings.API_HOST,
        port=settings.API_PORT,

        log_level=settings.LOG_LEVEL.lower(),

        reload=settings.DEBUG,
        reload_dirs=[f"{api_dir}/config", f"{api_dir}/core", f"{api_dir}/services"],
        reload_excludes=["__pycache__"]
    )
