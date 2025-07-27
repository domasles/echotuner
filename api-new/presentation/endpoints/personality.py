"""Personality-related endpoint implementations"""

import logging
from typing import Dict, Any
from fastapi import HTTPException, APIRouter, Request

from domain.auth.decorators import debug_only
from domain.shared.validation.validators import validate_user_request

from application import UserPersonalityResponse, FollowedArtistsResponse, ArtistSearchRequest, ArtistSearchResponse, UserContext
from domain.personality.service import personality_service
from infrastructure.database.repository import repository
from infrastructure.database.models.users import UserPersonality

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/personality", tags=["personality"])

@router.put("", response_model=UserPersonalityResponse)
@validate_user_request()
async def save_user_personality(request: Request, user_context: UserContext, validated_user_id: str = None):
    """Save user personality preferences"""

    try:
        logger.debug(f"Saving personality for user {validated_user_id}")

        # Unified system - use user_id directly
        success = await personality_service.save_user_personality_by_user_id(
            user_id=validated_user_id,
            user_context=user_context
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

@router.get("", response_model=Dict[str, Any])
@validate_user_request()
async def load_user_personality(request: Request, validated_user_id: str = None):
    """Load user personality preferences from user_id in headers"""
    try:
        user_context = await personality_service.get_user_personality_by_user_id(validated_user_id)

        if user_context:
            return {"user_context": user_context.model_dump()}
        else:
            return {"user_context": None}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to load personality")

@router.delete("")
@validate_user_request()
async def clear_user_personality(request: Request, validated_user_id: str = None):
    """Clear user personality preferences"""

    try:
        user_personality = await repository.get_by_field(UserPersonality, 'user_id', validated_user_id)
        
        if user_personality:
            success = await repository.delete(UserPersonality, user_personality.id)
        else:
            success = True  # Already doesn't exist

        return {"success": True, "message": "Personality cleared successfully"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to clear user personality: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear personality")

@router.get("/artists", response_model=FollowedArtistsResponse)
@validate_user_request()
async def get_artists(request: Request, validated_user_id: str = None):
    """Get user's followed artists from Spotify or search for artists"""

    try:
        # Check query parameters to determine what to return
        search_query = request.query_params.get('q')
        artist_type = request.query_params.get('type', 'followed')
        limit = int(request.query_params.get('limit', 50))

        if search_query:
            # Search for artists
            artists = await personality_service.search_artists(
                query=search_query,
                limit=limit
            )
            return ArtistSearchResponse(artists=artists)
        elif artist_type == 'followed':
            # Get followed artists
            artists = await personality_service.get_followed_artists_by_user_id(
                user_id=validated_user_id,
                limit=limit
            )
            return FollowedArtistsResponse(artists=artists)
        else:
            raise HTTPException(status_code=400, detail="Invalid artist type or missing search query")

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to get artists: {e}")
        if search_query:
            return ArtistSearchResponse(artists=[])
        else:
            return FollowedArtistsResponse(artists=[])
