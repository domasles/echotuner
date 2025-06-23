import logging
import uvicorn
import click
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from pathlib import Path

from core.models import PlaylistRequest, PlaylistResponse, RateLimitStatus
from config.settings import settings

from services.playlist_generator import PlaylistGeneratorService
from services.prompt_validator import PromptValidatorService
from services.rate_limiter import RateLimiterService
from services.data_loader import data_loader

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

app = FastAPI(
    title="EchoTuner API",
    description="AI-powered playlist generation with real-time song search",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter = RateLimiterService()
prompt_validator = PromptValidatorService()
playlist_generator = PlaylistGeneratorService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""

    logger.info("Starting EchoTuner API...")

    await rate_limiter.initialize()
    await prompt_validator.initialize()
    await playlist_generator.initialize()

    logger.info(f"Spotify Search: {'ENABLED' if playlist_generator.spotify_search.is_ready() else 'FALLBACK MODE'}")
    logger.info(f"AI Generation: {'OLLAMA' if settings.USE_OLLAMA else 'BASIC MODE'}")
    logger.info(f"Rate Limiting: {'ENABLED' if settings.DAILY_LIMIT_ENABLED else 'DISABLED'}")
    logger.info("EchoTuner API ready!")

@app.get("/")
async def root():
    return {
        "message": "EchoTuner API",
        "description": "AI-powered playlist generation with real-time song search",
        "endpoints": {
            "generate": "/generate-playlist",
            "refine": "/refine-playlist", 
            "health": "/health",
            "rate_limit": "/rate-limit-status/{device_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Check API health and service status"""

    return {
        "status": "healthy",
        "version": "1.0.1", 
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
        device_id = request.device_id

        if settings.DAILY_LIMIT_ENABLED and not rate_limiter.can_make_request(device_id):
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
            count=request.count or 30
        )

        if settings.DAILY_LIMIT_ENABLED:
            rate_limiter.record_request(device_id)
        
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
        device_id = request.device_id

        if settings.DAILY_LIMIT_ENABLED and not rate_limiter.can_refine_playlist(device_id):
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
            rate_limiter.record_refinement(device_id)
        
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
    """Get current rate limit status for a device"""

    try:
        return rate_limiter.get_status(device_id)

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
        reload_excludes=["data", "__pycache__", "venv", ".env", ".git", ".vscode"],
    )
