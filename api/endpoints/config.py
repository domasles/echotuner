"""Configuration-related endpoint implementations"""

import logging

from fastapi import HTTPException, APIRouter

from shared.constants import app_constants
from config.settings import settings

from services.data.data import data_loader

from core.auth.decorators import debug_only

from core.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/config", tags=["config"])

@router.get("/health")
async def health_check():
    """Check API health and service status"""

    return {
        "status": "healthy",
        "version": app_constants.API_VERSION
    }

@router.get("")
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
        },
        "features": {
            "auth_required": settings.AUTH_REQUIRED,
            "playlist_limit_enabled": settings.PLAYLIST_LIMIT_ENABLED,
        },
        "demo_mode": settings.DEMO
    }

@router.post("/reload")
@debug_only
async def reload_config():
    """Reload JSON configuration files without restarting the server"""
    try:
        data_loader.reload_cache()
        logger.info("Configuration files reloaded successfully")

        return {
            "message": "Configuration reloaded successfully",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {sanitized_error}")

async def root():
    """API root endpoint with welcome message and endpoint list"""
    return {
        "message": app_constants.API_WELCOME_MESSAGE,
        "description": "AI-powered playlist generation with real-time song search",
        "demo_mode": settings.DEMO,
        "demo_info": "Demo mode uses a shared Spotify account with device-specific experiences" if settings.DEMO else None,
        "endpoints": {
            "generate": "/playlist/generate",
            "update_draft": "/playlist/update-draft",
            "health": "/config/health",
            "rate_limit": "/auth/rate-limit-status",
            "auth_init": "/auth/init",
            "auth_callback": "/auth/callback",
            "auth_validate": "/auth/validate",
            "library": "/playlist/library",
            "add_to_spotify": "/spotify/create-playlist",
            "get_draft": "/playlist/drafts"
        }
    }
