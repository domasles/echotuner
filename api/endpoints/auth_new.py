"""
Authentication-related endpoint implementations
"""

import logging
import uuid
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

from core.models import (
    AuthInitRequest, AuthInitResponse, SessionValidationRequest, SessionValidationResponse, 
    RateLimitStatus, DeviceRegistrationRequest, DeviceRegistrationResponse,
    DemoPlaylistRefinementsRequest
)
from config.settings import settings
from services.auth_service import auth_service
from services.rate_limiter import rate_limiter_service
from services.template_service import template_service
from services.auth_middleware import auth_middleware
from services.database_service import db_service

logger = logging.getLogger(__name__)

async def auth_init(request: AuthInitRequest):
    """Initialize Spotify OAuth flow"""

    try:
        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")

        # Generate server-side device ID
        if settings.DEMO:
            # Use demo user ID for demo mode
            device_id = f"demo_user_{int(datetime.now().timestamp() * 1000)}"
        else:
            # Generate proper UUID for normal mode
            device_id = str(uuid.uuid4())

        if not await auth_service.validate_device(device_id, update_last_seen=False):
            try:
                await auth_service.register_device_with_id(
                    device_id=device_id,
                    platform=request.platform
                )

            except Exception as e:
                logger.error(f"Failed to auto-register device: {e}")
                raise HTTPException(status_code=500, detail="Failed to register device")

        auth_url, state = auth_service.generate_auth_url(device_id, request.platform)

        await auth_service.store_auth_state(state, device_id, request.platform)
        return AuthInitResponse(auth_url=auth_url, state=state, device_id=device_id)

    except Exception as e:
        logger.error(f"Auth init failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize authentication")

async def auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle Spotify OAuth callback"""

    try:
        if error:
            logger.warning(f"OAuth error: {error}")
            html_content = template_service.render_template("auth_error.html", error=error)

            return HTMLResponse(content=html_content)

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing authorization code or state")

        # Validate state and get device info
        device_info = await auth_service.validate_auth_state(state)
        if not device_info:
            raise HTTPException(status_code=400, detail="Invalid or expired auth state")

        result = await auth_service.handle_spotify_callback(code, state, device_info)

        if not result:
            raise HTTPException(status_code=400, detail="Failed to create session")

        session_id = result
        html_content = template_service.render_template("auth_success.html", session_id=session_id, device_id=device_info['device_id'])
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Auth callback failed: {e}")
        html_content = template_service.render_template("auth_error.html")

        return HTMLResponse(content=html_content)

async def validate_session(request: SessionValidationRequest):
    """Validate session"""

    try:
        # Use validate_session_and_get_user instead of basic validate_session
        # This ensures mode mismatches are also checked
        user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)
        
        if user_info is None:
            # Check if it's a basic session validation failure vs mode mismatch
            basic_valid = await auth_service.validate_session(request.session_id, request.device_id)
            
            if basic_valid:
                # Session exists but mode mismatch - return 401
                raise HTTPException(status_code=401, detail="Session invalid due to server mode mismatch")
            else:
                # Basic session validation failed - return 401
                raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return SessionValidationResponse(valid=True)

    except HTTPException:
        # Re-raise HTTP exceptions (like 401)
        raise
    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        raise HTTPException(status_code=500, detail="Session validation failed")

async def check_session(request):
    """Check if a session exists for the given device ID (for desktop polling)"""

    try:
        device_id = request.headers.get('device_id')
        if not device_id:
            return {"message": "Device ID required in headers", "success": False}

        session_id = await auth_service.get_session_by_device(device_id)

        if session_id:
            return {"session_id": session_id, "device_id": device_id}

        else:
            return {"session_id": None}

    except Exception as e:
        logger.error(f"Check session failed: {e}")
        return {"session_id": None}

async def get_authenticated_rate_limit_status(request: SessionValidationRequest):
    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        
        # For demo accounts, use device_id for rate limiting (per device)
        # For normal accounts, use spotify_user_id for rate limiting (shared across devices)
        if user_info and user_info.get('account_type') == 'demo':
            rate_limit_key = request.device_id
        else:
            rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id
            
        return await rate_limiter_service.get_status(rate_limit_key)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Rate limit status error: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {str(e)}")

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

async def logout(request):
    """Logout and completely clear all device data"""

    try:
        session_id = request.headers.get('session_id')
        device_id = request.headers.get('device_id')

        if not device_id:
            return {"message": "Device ID required for logout", "success": False}

        # Completely invalidate all data for this device
        await auth_service.invalidate_device_completely(device_id)
        
        logger.info(f"Successfully cleared all data for device {device_id[:8]}...")
        return {"message": "Logged out successfully and cleared device data", "success": True}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"message": "Logout failed", "success": False, "error": str(e)}

async def logout_all(request):
    """Logout from all devices for the current user"""
    try:
        session_id = request.headers.get('session_id')
        device_id = request.headers.get('device_id')
        
        if not session_id:
            return {"message": "No session provided", "success": False}

        user_info = await auth_service.validate_session_and_get_user(session_id, device_id or "")

        if user_info:
            spotify_user_id = user_info.get('spotify_user_id')
            await auth_service.revoke_all_user_sessions(spotify_user_id)
            logger.info(f"Logged out all sessions for user {spotify_user_id}")

            return {"message": "Logged out from all devices successfully", "success": True}

        else:
            return {"message": "Invalid session", "success": False}

    except Exception as e:
        logger.error(f"Logout all failed: {e}")
        return {"message": "Logout all failed", "success": False, "error": str(e)}

async def cleanup_sessions():
    """Clean up expired sessions and auth attempts (debug only)"""

    try:
        await auth_service.cleanup_expired_sessions()
        await db_service.cleanup_expired_auth_attempts()

        return {"message": "Cleanup completed successfully"}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

async def get_account_type(session_id: str):
    """Get account type for a session"""
    try:
        account_type = await auth_service.get_account_type(session_id)
        if account_type is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"account_type": account_type}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account type: {e}")
        raise HTTPException(status_code=500, detail="Failed to get account type")

async def get_auth_mode():
    """Get current authentication mode"""
    return {
        "mode": "demo" if settings.DEMO else "normal",
        "demo": settings.DEMO
    }

async def get_demo_playlist_refinements(request: DemoPlaylistRefinementsRequest):
    """Get refinement count for a specific demo playlist"""
    
    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        
        # Only allow demo accounts to use this endpoint
        if not user_info or user_info.get('account_type') != 'demo':
            raise HTTPException(status_code=403, detail="This endpoint is only available for demo accounts")
        
        refinements_used = await db_service.get_demo_playlist_refinements(request.playlist_id)
        
        return {
            "playlist_id": request.playlist_id,
            "refinements_used": refinements_used,
            "max_refinements": settings.MAX_REFINEMENTS_PER_PLAYLIST,
            "can_refine": refinements_used < settings.MAX_REFINEMENTS_PER_PLAYLIST
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Demo playlist refinements error: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting demo playlist refinements: {str(e)}")
