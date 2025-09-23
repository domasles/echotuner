"""
New Authentication Endpoints.
Unified OAuth authentication with polling support.
"""

import logging
import uuid

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

from infrastructure.rate_limiting.limit_service import rate_limiter_service
from infrastructure.template.service import template_service
from infrastructure.auth.service import oauth_service

from domain.shared.validation.decorators import validate_request_headers
from domain.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/init")
async def auth_init(request: Request, app_id: str = Header(None, alias="X-Session-UUID")):
    """Initialize authentication flow based on mode and app UUID."""

    try:
        if not app_id:
            raise HTTPException(status_code=400, detail="X-Session-UUID header is required")

        try:
            uuid.UUID(app_id)

        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Session-UUID format")

        await oauth_service.create_auth_session(app_id)

        if settings.SHARED:
            owner_creds = await oauth_service.get_owner_credentials()
            
            if not owner_creds:
                return JSONResponse({
                    "auth_url": f"{request.base_url}auth/setup",
                    "session_uuid": app_id,
                    "action": "setup_required",
                    "message": "Owner setup required. An external browser window will open to complete the setup process."
                })

            else:
                auth_url = oauth_service.get_auth_url('google', app_id)

                return JSONResponse({
                    "auth_url": auth_url,
                    "session_uuid": app_id
                })

        else:
            auth_url = oauth_service.get_auth_url('spotify', app_id)

            return JSONResponse({
                "auth_url": auth_url,
                "session_uuid": app_id
            })

    except Exception as e:
        logger.error(f"Auth init failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication initialization failed")

@router.get("/setup")
async def setup_page(request: Request):
    """Setup page for owner credentials (shared mode only)."""

    if not settings.SHARED:
        raise HTTPException(status_code=404, detail="Setup not available in normal mode")

    owner_creds = await oauth_service.get_owner_credentials()

    if owner_creds:
        return JSONResponse({"message": "Setup already completed"})

    auth_url = oauth_service.get_auth_url('spotify')
    return RedirectResponse(url=auth_url)

@router.get("/spotify/callback")
async def spotify_callback(code: str, state: str = None, error: str = None):
    """Handle Spotify OAuth callback."""

    if error:
        logger.error(f"Spotify OAuth error: {error}")

        html_content = template_service.render_template(
            "html/auth_error.html",
            error_message="Authentication failed. Please try again.",
            error_detail=""
        )

        return HTMLResponse(content=html_content, status_code=400)

    try:
        if settings.SHARED and not state:
            await oauth_service.store_owner_credentials(code)
            html_content = template_service.render_template("html/auth_success.html")
            return HTMLResponse(content=html_content)

        else:
            result = await oauth_service.handle_spotify_callback(code, state)
            html_content = template_service.render_template("html/auth_success.html")
            return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Spotify callback failed: {e}")

        html_content = template_service.render_template(
            "html/auth_error.html",
            error_message="Authentication failed. Please try again.",
            error_detail=""
        )

        return HTMLResponse(content=html_content, status_code=500)

@router.get("/google/callback")
async def google_callback(code: str, state: str = None, error: str = None):
    """Handle Google OAuth callback."""

    if error:
        logger.error(f"Google OAuth error: {error}")

        html_content = template_service.render_template(
            "html/auth_error.html",
            error_message="Authentication failed. Please try again.",
            error_detail=""
        )

        return HTMLResponse(content=html_content, status_code=400)

    try:
        result = await oauth_service.handle_google_callback(code, state)
        html_content = template_service.render_template("html/auth_success.html")
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Google callback failed: {e}")

        html_content = template_service.render_template(
            "html/auth_error.html",
            error_message="Authentication failed. Please try again.",
            error_detail=""
        )

        return HTMLResponse(content=html_content, status_code=500)

@router.get("/status")
async def auth_status(app_id: str = Header(None, alias="X-Session-UUID")):
    """Check authentication session status for polling."""

    if not app_id:
        raise HTTPException(status_code=400, detail="X-Session-UUID header required")

    try:
        uuid.UUID(app_id)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Session-UUID format")

    try:
        user_id = await oauth_service.check_auth_session(app_id)

        if user_id:
            return JSONResponse({"status": "completed", "user_id": user_id})

        else:
            return JSONResponse({"status": "pending"})

    except Exception as e:
        logger.error(f"Session status check failed: {e}")
        raise HTTPException(status_code=500, detail="Session status check failed")
