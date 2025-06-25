import asyncio
import logging
import uvicorn
import click
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from contextlib import asynccontextmanager
from pathlib import Path

from core.models import PlaylistRequest, PlaylistResponse, RateLimitStatus, AuthInitRequest, AuthInitResponse, SessionValidationRequest, SessionValidationResponse
from config.settings import settings

from services.playlist_generator import PlaylistGeneratorService
from services.prompt_validator import PromptValidatorService
from services.rate_limiter import RateLimiterService
from services.auth_service import AuthService
from services.data_loader import data_loader
from services.template_service import template_service

class CustomFormatter(logging.Formatter):
    def format(self, record):
        raw_level = record.levelname
        color = settings.LOGGER_COLORS.get(raw_level, None)

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

rate_limiter = RateLimiterService()
prompt_validator = PromptValidatorService()
playlist_generator = PlaylistGeneratorService()
auth_service = AuthService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""

    logger.info("Starting EchoTuner API...")
    
    try:
        init_tasks = [
            rate_limiter.initialize(),
            prompt_validator.initialize(),
            playlist_generator.initialize(),
            auth_service.initialize()
        ]

        cache_task = asyncio.create_task(preload_data_cache())

        await asyncio.gather(*init_tasks)

        logger.info(f"Spotify Search: {'ENABLED' if playlist_generator.spotify_search.is_ready() else 'DISABLED'}")
        logger.info(f"AI Generation: {'OLLAMA' if settings.USE_OLLAMA else 'BASIC MODE'}")
        logger.info(f"Rate Limiting: {'ENABLED' if settings.DAILY_LIMIT_ENABLED else 'DISABLED'}")
        logger.info(f"Auth Service: {'ENABLED' if auth_service.is_ready() else 'DISABLED'}")
        
    except Exception as e:
        logger.error(f"Failed to initialize EchoTuner API: {e}")
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
        logger.info("Data cache preloaded successfully!")
        
    except Exception as e:
        logger.warning(f"Cache preloading failed (non-critical): {e}")

app = FastAPI(
    title="EchoTuner API",
    description="AI-powered playlist generation with real-time song search",
    version="1.2.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "EchoTuner API",
        "description": "AI-powered playlist generation with real-time song search",
        "endpoints": {
            "generate": "/generate-playlist",
            "refine": "/refine-playlist", 
            "health": "/health",
            "rate_limit": "/rate-limit-status/{device_id}",
            "auth_init": "/auth/init",
            "auth_callback": "/auth/callback",
            "auth_validate": "/auth/validate"
        }
    }

@app.post("/auth/init", response_model=AuthInitResponse)
async def auth_init(request: AuthInitRequest):
    """Initialize Spotify OAuth flow"""
    try:
        logger.info(f"Auth init request: device_id={request.device_id}, platform={request.platform}")
        
        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")
        
        auth_url, state = auth_service.generate_auth_url(request.device_id, request.platform)
        await auth_service.store_auth_state(state, request.device_id, request.platform)
        
        logger.info(f"Generated auth URL for device {request.device_id}")
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
        html_content = template_service.render_template("auth_failed.html")

        return HTMLResponse(content=html_content)

@app.post("/auth/validate", response_model=SessionValidationResponse)
async def validate_session(request: SessionValidationRequest):
    """Validate session"""

    try:
        logger.info(f"Session validation request: session_id={request.session_id[:8]}..., device_id={request.device_id}")
        is_valid = await auth_service.validate_session(request.session_id, request.device_id)
        logger.info(f"Session validation result: {is_valid}")

        return SessionValidationResponse(valid=is_valid)
        
    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        raise HTTPException(status_code=500, detail="Session validation failed")

@app.get("/auth/check-session/{device_id}")
async def check_session(device_id: str):
    """Check if a session exists for the given device ID (for desktop polling)"""

    try:
        logger.info(f"Checking session for device: {device_id}")
        session_id = await auth_service.get_session_by_device(device_id)
        
        if session_id:
            logger.info(f"Found session for device {device_id}")
            return {"session_id": session_id}
        
        else:
            return {"session_id": None}
            
    except Exception as e:
        logger.error(f"Check session failed: {e}")
        return {"session_id": None}

async def require_auth(request: PlaylistRequest):
    """Middleware function to check authentication and return user info"""

    if not settings.AUTH_REQUIRED:
        return None
        
    if not hasattr(request, 'session_id') or not request.session_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user_info

@app.get("/health")
async def health_check():
    """Check API health and service status"""

    if settings.DEBUG:
        return {
            "status": "healthy",
            "version": "1.2.1", 
            "services": {
                "prompt_validator": prompt_validator.is_ready(),
                "playlist_generator": playlist_generator.is_ready(),
                "rate_limiter": rate_limiter.is_ready()
            },
            "features": {
                "spotify_search": playlist_generator.spotify_search.is_ready(),
                "ai_generation": settings.USE_OLLAMA,
                "rate_limiting": settings.DAILY_LIMIT_ENABLED
            }
        }
    
    else:
        logger.warning("API health check is disabled in production mode")
        raise HTTPException(status_code=403, detail="API health check is disabled in production mode")

@app.post("/reload-config")
async def reload_config():
    """Reload JSON configuration files without restarting the server"""

    if settings.DEBUG:
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
        
    else:
        logger.warning("Configuration reload is disabled in production mode")
        raise HTTPException(status_code=403, detail="Configuration reload is disabled in production mode")

@app.post("/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(request: PlaylistRequest):
    """Generate a playlist using AI-powered real-time song search"""

    try:
        user_info = await require_auth(request)
        rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id

        if settings.DAILY_LIMIT_ENABLED and not await rate_limiter.can_make_request(rate_limit_key):
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit of {settings.MAX_PLAYLISTS_PER_DAY} playlists reached. Try again tomorrow."
            )

        is_valid_prompt = await prompt_validator.validate_prompt(request.prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The prompt doesn't seem to be related to music or mood. Please try a different description."
            )

        songs = await playlist_generator.generate_playlist(
            prompt=request.prompt,
            user_context=request.user_context,
            count=request.count if settings.DEBUG else settings.MAX_SONGS_PER_PLAYLIST
        )

        if settings.DAILY_LIMIT_ENABLED:
            await rate_limiter.record_request(rate_limit_key)
        
        return PlaylistResponse(
            songs=songs,
            generated_from=request.prompt,
            total_count=len(songs),
            is_refinement=False
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

        if settings.DAILY_LIMIT_ENABLED and not await rate_limiter.can_refine_playlist(rate_limit_key):
            raise HTTPException(
                status_code=429,
                detail=f"Maximum of {settings.MAX_REFINEMENTS_PER_PLAYLIST} AI refinements reached for this playlist."
            )

        is_valid_prompt = await prompt_validator.validate_prompt(request.prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The refinement request doesn't seem to be music-related. Please try a different description."
            )

        songs = await playlist_generator.refine_playlist(
            original_songs=request.current_songs or [],
            refinement_prompt=request.prompt,
            user_context=request.user_context,
            count=request.count or 30
        )

        if settings.DAILY_LIMIT_ENABLED:
            await rate_limiter.record_refinement(rate_limit_key)
        
        return PlaylistResponse(
            songs=songs,
            generated_from=request.prompt,
            total_count=len(songs),
            is_refinement=True
        )
        
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining playlist: {str(e)}")

@app.get("/rate-limit-status/{device_id}", response_model=RateLimitStatus)
async def get_rate_limit_status(device_id: str):
    """Get current rate limit status for a device (legacy endpoint - insecure)"""
    logger.warning(f"Using insecure rate limit endpoint for device: {device_id}")

    try:
        return await rate_limiter.get_status(device_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {str(e)}")

@app.post("/auth/rate-limit-status", response_model=RateLimitStatus)
async def get_authenticated_rate_limit_status(request: SessionValidationRequest):
    """Get current rate limit status using authenticated session"""

    try:
        user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        rate_limit_key = user_info["spotify_user_id"]
        
        return await rate_limiter.get_status(rate_limit_key)

    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {str(e)}")

if __name__ == "__main__":
    logger.info("EchoTuner API - AI-Powered Playlist Generation")

    uvicorn.run(
        "main:app",

        host=settings.API_HOST,
        port=settings.API_PORT,

        log_level=settings.LOG_LEVEL.lower(),

        reload=settings.DEBUG,
        reload_dirs=[f"{api_dir}/config", f"{api_dir}/core", f"{api_dir}/services"],
        reload_excludes=["__pycache__"]
    )
