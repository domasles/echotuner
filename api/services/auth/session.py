"""
Session manager for EchoTuner API.
Handles user session management and device registration.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from core.singleton import SingletonServiceBase
from core.validation.validators import UniversalValidator
from core.service.decorators import service_bool_operation, service_optional_operation

from services.database.database import db_service

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
            
            await db_service.create_session(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            return False

    @service_optional_operation("validate_session")
    async def validate_session(self, session_id: str, device_id: str) -> Optional[Dict]:
        """Validate a user session."""
        try:
            session = await db_service.get_session(session_id, device_id)
            if not session:
                return None
            
            if session.expires_at < datetime.utcnow():
                await db_service.delete_session(session_id)
                return None
            
            return {
                "user_id": session.user_id,
                "device_id": session.device_id,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token
            }
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return None

    @service_bool_operation("refresh_session")
    async def refresh_session(self, session_id: str, new_access_token: str, new_refresh_token: str) -> bool:
        """Refresh a user session with new tokens."""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            return await db_service.update_session(
                session_id=session_id,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")
            return False

    @service_bool_operation("delete_session")
    async def delete_session(self, session_id: str) -> bool:
        """Delete a user session."""
        try:
            return await db_service.delete_session(session_id)
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

session_manager = SessionManager()
