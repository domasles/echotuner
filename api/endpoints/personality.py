"""Personality-related endpoint implementations"""

import logging
from fastapi import HTTPException

from models import UserPersonalityRequest, UserPersonalityResponse, UserPersonalityClearRequest, FollowedArtistsResponse, ArtistSearchRequest, ArtistSearchResponse
from services.personality_service import personality_service
from services.auth_middleware import auth_middleware
from services.database_service import db_service

logger = logging.getLogger(__name__)

async def save_user_personality(request: UserPersonalityRequest):
    """Save user personality preferences"""

    try:
        logger.debug(f"Saving personality for session {request.session_id}")

        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)

        success = await personality_service.save_user_personality(
            session_id=request.session_id,
            device_id=request.device_id,
            user_context=request.user_context
        )

        if success:
            logger.debug("Personality saved successfully")
            return UserPersonalityResponse(success=True, message="Personality saved successfully")

        else:
            logger.error("Personality save failed")
            raise HTTPException(status_code=500, detail="Failed to save personality")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to save user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to save personality")

async def load_user_personality(request):
    try:
        user_info = await auth_middleware.validate_session_from_headers(request)

        user_context = await personality_service.get_user_personality(
            session_id=request.headers.get('session_id'),
            device_id=request.headers.get('device_id')
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

async def clear_user_personality(request: UserPersonalityClearRequest):
    """Clear user personality preferences"""

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
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

async def get_followed_artists(request, limit: int = 50):
    """Get user's followed artists from Spotify"""

    try:
        user_info = await auth_middleware.validate_session_from_headers(request)

        artists = await personality_service.get_followed_artists(
            session_id=request.headers.get('session_id'),
            device_id=request.headers.get('device_id'),
            limit=limit
        )

        return FollowedArtistsResponse(artists=artists)

    except HTTPException:
        raise

    except Exception as e:
        logger.warning(f"Failed to get followed artists: {e}")
        return FollowedArtistsResponse(artists=[])

async def search_artists(request: ArtistSearchRequest):
    """Search for artists on Spotify"""

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)

        artists = await personality_service.search_artists(
            session_id=request.session_id,
            device_id=request.device_id,
            query=request.query,
            limit=request.limit or 20
        )

        return ArtistSearchResponse(artists=artists)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to search artists: {e}")
        raise HTTPException(status_code=500, detail="Failed to search artists")
