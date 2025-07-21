"""Authentication-related endpoint implementations"""

import logging
import uuid

from fastapi import HTTPException, Request, APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime
from sqlalchemy import delete

from application import AuthInitRequest, AuthInitResponse, SessionValidationRequest, SessionValidationResponse, DeviceRegistrationRequest, DeviceRegistrationResponse, RateLimitStatus, AccountTypeResponse

from infrastructure.config.settings import settings
from infrastructure.database import get_session
from infrastructure.database.models import AuthAttempt

from infrastructure.rate_limiting.ip_limit_service import ip_rate_limiter_service
from infrastructure.rate_limiting.limit_service import rate_limiter_service
from infrastructure.template.service import template_service
from domain.auth.middleware import auth_middleware
from domain.auth.service import auth_service
from domain.auth.decorators import debug_only

from domain.shared.validation.validators import UniversalValidator, validate_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers."""

    forwarded_for = request.headers.get("X-Forwarded-For")
    real_ip = request.headers.get("X-Real-IP")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host
    
    return "unknown"

@router.post("/init", response_model=AuthInitResponse)
@validate_request('device_id')
async def auth_init(request: AuthInitRequest, http_request: Request):
    """Initialize Spotify OAuth flow"""

    try:
        client_ip = get_client_ip(http_request)

        if await ip_rate_limiter_service.is_ip_blocked(client_ip):
            remaining = await ip_rate_limiter_service.get_remaining_attempts(client_ip)

            raise HTTPException(
                status_code=429, 
                detail=f"Too many authentication attempts. Try again later. Remaining attempts: {remaining}"
            )

        if not auth_service.is_ready():
            logger.error("Auth service not ready")
            raise HTTPException(status_code=503, detail="Authentication service not available")

        if settings.DEMO:
            # In demo mode, check if we already have owner's token
            if auth_service.has_demo_owner_token():
                # Owner token exists, create bypass session and redirect directly to success
                device_id = f"demo_user_{int(datetime.now().timestamp() * 1000)}"
                
                if not await auth_service.validate_device(device_id, update_last_seen=False):
                    try:
                        device_data = {
                            'device_id': device_id,
                            'platform': request.platform,
                            'app_version': getattr(request, 'app_version', None),
                            'device_fingerprint': getattr(request, 'device_fingerprint', None),
                            'registration_timestamp': int(datetime.now().timestamp()),
                            'last_seen_timestamp': int(datetime.now().timestamp()),
                            'is_active': True
                        }
                        await auth_service.register_device(device_data)
                    except Exception as e:
                        logger.error(f"Failed to auto-register device: {e}")
                        raise HTTPException(status_code=500, detail="Failed to register device")
                
                # Create bypass session
                session_id = await auth_service.create_demo_bypass_session(device_id, request.platform)
                
                # Return direct callback URL that will show success page
                callback_url = f"{settings.SPOTIFY_REDIRECT_URI}?demo_bypass=true&session_id={session_id}&device_id={device_id}"
                return AuthInitResponse(auth_url=callback_url, state="demo_bypass", device_id=device_id)
            else:
                # First time - need real OAuth to get owner's token
                device_id = f"demo_user_{int(datetime.now().timestamp() * 1000)}"

        else:
            device_id = str(uuid.uuid4())

        if not await auth_service.validate_device(device_id, update_last_seen=False):
            try:
                device_data = {
                    'device_id': device_id,
                    'platform': request.platform,
                    'app_version': getattr(request, 'app_version', None),
                    'device_fingerprint': getattr(request, 'device_fingerprint', None),
                    'registration_timestamp': int(datetime.now().timestamp()),
                    'last_seen_timestamp': int(datetime.now().timestamp()),
                    'is_active': True
                }
                await auth_service.register_device(device_data)

            except Exception as e:
                logger.error(f"Failed to auto-register device: {e}")
                raise HTTPException(status_code=500, detail="Failed to register device")

        auth_url, state = await auth_service.generate_auth_url(device_id, request.platform)

        await auth_service.store_auth_state(state, device_id, request.platform)
        return AuthInitResponse(auth_url=auth_url, state=state, device_id=device_id)

    except Exception as e:
        logger.error(f"Auth init failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize authentication")

@router.get("/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None, http_request: Request = None, demo_bypass: str = None, session_id: str = None, device_id: str = None):
    """Handle Spotify OAuth callback"""

    try:
        client_ip = get_client_ip(http_request) if http_request else "unknown"
        
        # Handle demo bypass mode
        if demo_bypass == "true" and session_id and device_id:
            logger.info(f"Demo bypass authentication for device {device_id[:8]}...")
            
            html_content = template_service.render_template("html/auth_success.html", session_id=session_id, device_id=device_id)
            return HTMLResponse(content=html_content)
        
        if error:
            logger.warning(f"OAuth error from IP {client_ip}: {error}")
            await ip_rate_limiter_service.record_failed_attempt(client_ip, "oauth_error")

            html_content = template_service.render_template(
                "html/auth_error.html", 
                error_detail=f'<p class="auth-error-detail">Error: {error}</p>',
                error_message="Please try again."
            )

            return HTMLResponse(content=html_content)

        if not code or not state:
            await ip_rate_limiter_service.record_failed_attempt(client_ip, "invalid_params")
            raise HTTPException(status_code=400, detail="Missing authorization code or state")

        device_info = await auth_service.validate_auth_state(state)

        if not device_info:
            await ip_rate_limiter_service.record_failed_attempt(client_ip, "invalid_state")
            raise HTTPException(status_code=400, detail="Invalid or expired auth state")

        result = await auth_service.handle_spotify_callback(code, state, device_info)

        if not result:
            await ip_rate_limiter_service.record_failed_attempt(client_ip, "callback_failed")
            raise HTTPException(status_code=400, detail="Failed to create session")

        await ip_rate_limiter_service.clear_ip_attempts(client_ip)
        
        session_id = result
        html_content = template_service.render_template("html/auth_success.html", session_id=session_id, device_id=device_info['device_id'])

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Auth callback failed: {e}")

        html_content = template_service.render_template(
            "html/auth_error.html",
            error_detail="",
            error_message="An error occurred during authentication."
        )

        return HTMLResponse(content=html_content)

@router.post("/validate", response_model=SessionValidationResponse)
@validate_request('session_id', 'device_id')
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

    except ValueError as e:
        logger.warning(f"Session validation input error: {e}")
        raise HTTPException(status_code=400, detail="Invalid input parameters")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        raise HTTPException(status_code=500, detail="Session validation failed")

@router.get("/check-session")
async def check_session(request: Request, device_id: str = None):
    """Check if a session exists for the given device ID (for desktop polling)"""

    try:
        # Try to get device_id from query parameter first, then headers
        if not device_id:
            device_id = request.headers.get('device_id')

        if not device_id:
            return {"message": "Device ID required in headers or query parameter", "success": False}

        logger.info(f"Check session for device_id: {device_id}")
        session_info = await auth_service.get_session_by_device(device_id)
        logger.info(f"Session info result: {session_info}")

        if session_info:
            logger.info(f"Returning session_id: {session_info['session_id']}")
            return {"session_id": session_info['session_id'], "device_id": device_id}

        else:
            logger.info("No session found, returning None")
            return {"session_id": None}

    except Exception as e:
        logger.error(f"Check session failed: {e}")
        return {"session_id": None}

@router.post("/rate-limit-status", response_model=RateLimitStatus)
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
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=500, detail=f"Error checking rate limit: {sanitized_error}")

@router.post("/register-device", response_model=DeviceRegistrationResponse)
@validate_request('device_id')
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

@router.post("/logout")
async def logout(request: Request):
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

@router.post("/cleanup")
@debug_only
async def cleanup_sessions():
    """Clean up expired sessions and auth attempts"""

    try:
        await auth_service.cleanup_expired_sessions()
        
        # Inline cleanup of expired auth attempts
        current_time = int(datetime.now().timestamp())
        async with get_session() as session:
            await session.execute(
                delete(AuthAttempt).where(AuthAttempt.expires_at < current_time)
            )
            await session.commit()

        return {"message": "Cleanup completed successfully"}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

@router.post("/account-type", response_model=AccountTypeResponse)
async def get_account_type(request: SessionValidationRequest):
    """Get account type for a session."""

    try:
        account_type = await auth_service.get_account_type(request.session_id)

        if account_type:
            return AccountTypeResponse(account_type=account_type)

        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Account type check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get account type")

@router.get("/demo-status")
async def get_demo_status():
    """Get demo mode status and owner token availability (debug endpoint)."""
    
    try:
        return {
            "demo_mode": settings.DEMO,
            "has_owner_token": auth_service.has_demo_owner_token() if settings.DEMO else False,
            "auth_required": settings.AUTH_REQUIRED
        }
    
    except Exception as e:
        logger.error(f"Demo status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get demo status")

@router.get("/mode")
async def get_auth_mode():
    """Get current authentication mode"""

    return {
        "mode": "demo" if settings.DEMO else "normal",
        "demo": settings.DEMO
    }

