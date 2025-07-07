"""Authentication-related endpoint implementations"""

import logging
import uuid

from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from datetime import datetime

from core.models import AuthInitRequest, AuthInitResponse, SessionValidationRequest, SessionValidationResponse, DeviceRegistrationRequest, DeviceRegistrationResponse, DemoPlaylistRefinementsRequest

from config.settings import settings

from services.template_service import template_service
from services.rate_limiter import rate_limiter_service
from services.auth_middleware import auth_middleware
from services.database_service import db_service
from services.auth_service import auth_service

logger = logging.getLogger(__name__)

async def auth_init(request: AuthInitRequest):
    """Initialize Spotify OAuth flow"""

    try:
        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")

        if settings.DEMO:
            device_id = f"demo_user_{int(datetime.now().timestamp() * 1000)}"
        else:
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
        user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)
        
        if user_info is None:
            basic_valid = await auth_service.validate_session(request.session_id, request.device_id)
            
            if basic_valid:
                raise HTTPException(status_code=401, detail="Session invalid due to server mode mismatch")

            else:
                raise HTTPException(status_code=401, detail="Invalid or expired session")

        return SessionValidationResponse(valid=True)

    except HTTPException:
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
        device_id = request.headers.get('device_id')

        if not device_id:
            return {"message": "Device ID required for logout", "success": False}

        await auth_service.invalidate_device_completely(device_id)
        
        logger.debug(f"Successfully cleared all data for device {device_id[:8]}...")
        return {"message": "Logged out successfully and cleared device data", "success": True}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"message": "Logout failed", "success": False, "error": str(e)}

async def cleanup_sessions():
    """Clean up expired sessions and auth attempts"""

    try:
        await auth_service.cleanup_expired_sessions()
        await db_service.cleanup_expired_auth_attempts()

        return {"message": "Cleanup completed successfully"}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

async def get_account_type(request: SessionValidationRequest):
    """Get account type for a session"""

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)

        if not user_info:
            raise HTTPException(status_code=404, detail="Session not found")

        account_type = user_info.get('account_type', 'normal')
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
