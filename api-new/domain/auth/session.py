"""
Session manager for EchoTuner API.
Handles user session management and device registration.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from application.core.singleton import SingletonServiceBase
from domain.shared.validation.validators import UniversalValidator
from application.core.service.decorators import service_bool_operation, service_optional_operation

# Import the auth service for session operations
from domain.auth.service import auth_service

logger = logging.getLogger(__name__)

class SessionManager(SingletonServiceBase):
    """Service for managing user sessions and device registration."""

    def __init__(self):
        super().__init__()
    
    def _setup_service(self):
        """Initialize the SessionManager."""
        self._log_initialization("Session manager initialized successfully", logger)

    @service_bool_operation("generate_session")
    async def generate_session(self, user_id: str, device_id: str, access_token: str, refresh_token: str) -> bool:
        """Generate a new user session."""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            session_data = {
                'session_id': session_id,
                'device_id': device_id,
                'spotify_user_id': user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': int(expires_at.timestamp()),
                'created_at': int(datetime.utcnow().timestamp()),
                'last_used_at': int(datetime.utcnow().timestamp()),
                'account_type': 'normal',
                'platform': 'unknown'  # Default platform
            }
            
            await auth_service.create_session(session_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            return False

    @service_optional_operation("validate_session")
    async def validate_session(self, session_id: str, device_id: str) -> Optional[Dict]:
        """Validate a user session."""
        try:
            session_info = await auth_service.get_session_info(device_id)
            if not session_info:
                return None
            
            # Auth service already handles expiration internally
            return {
                "user_id": session_info.get('spotify_user_id', ''),
                "device_id": session_info.get('device_id', ''),
                "access_token": session_info.get('access_token', ''),
                "refresh_token": session_info.get('refresh_token', '')
            }
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return None

    @service_bool_operation("refresh_session")
    async def refresh_session(self, session_id: str, new_access_token: str, new_refresh_token: str) -> bool:
        """Refresh a user session with new tokens."""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # For now, simply return True as auth service handles token refreshing
            # TODO: Implement session update via auth service
            return True
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")
            return False

    @service_bool_operation("delete_session")
    async def delete_session(self, session_id: str) -> bool:
        """Delete a user session."""
        try:
            await auth_service.invalidate_session(session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

session_manager = SessionManager()
