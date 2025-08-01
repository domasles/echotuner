"""User profile endpoints."""

from fastapi import APIRouter, Request, HTTPException
from application.user_models import UserPersonalityResponse
from domain.shared.validation.decorators import validate_request_headers
from infrastructure.database.repository import repository
from infrastructure.database.models.auth import UserAccount
from infrastructure.auth.service import oauth_service
from infrastructure.rate_limiting.limit_service import rate_limiter_service
from domain.config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile")
@validate_request_headers()
async def get_user_profile(request: Request, validated_user_id: str = None):
    """Get user profile information."""
    
    try:
        # Get user account information
        user_account = await repository.get_by_field(UserAccount, "user_id", validated_user_id)
        if not user_account:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract provider
        provider = user_account.provider
        
        return {
            "user_id": user_account.user_id,
            "provider": user_account.provider,
            "display_name": user_account.display_name or "Unknown",
            "created_at": user_account.created_at.isoformat() if user_account.created_at else None,
            "last_used_at": user_account.last_used_at.isoformat() if user_account.last_used_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile information")

@router.get("/rate-limit-status")
@validate_request_headers()
async def get_rate_limit_status(request: Request, validated_user_id: str = None):
    """Get current rate limit status for authenticated user."""
    
    try:
        user_id = validated_user_id
        
        # Get rate limit status using the rate limiter service
        status = await rate_limiter_service.get_status(user_id)
        
        return {
            "user_id": status.user_id,
            "requests_made_today": status.requests_made_today,
            "max_requests_per_day": status.max_requests_per_day,
            "can_make_request": status.can_make_request,
            "playlist_limit_enabled": settings.PLAYLIST_LIMIT_ENABLED
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")
