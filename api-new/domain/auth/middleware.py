"""
Auth middleware for FastAPI.
Handles user authentication and session validation.
"""

import logging

from fastapi import HTTPException, Request
from typing import Optional, Dict

from application.core.singleton import SingletonServiceBase

from domain.auth.service import auth_service

logger = logging.getLogger(__name__)

class AuthMiddleware(SingletonServiceBase):
    """Middleware for validating user sessions and managing authentication."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the AuthMiddleware with the AuthService."""

        self.auth_service = auth_service
        self._log_initialization("Auth middleware initialized successfully", logger)

    async def validate_session_from_request(self, session_id: str, device_id: str) -> Dict[str, str]:
        if not session_id or not device_id:
            raise HTTPException(status_code=422, detail="Missing session_id or device_id")

        user_info = await self.auth_service.validate_session_and_get_user(session_id, device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return user_info

    async def get_access_token_for_session(self, session_id: str) -> Optional[str]:
        try:
            return await self.auth_service.get_access_token(session_id)

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None

    async def validate_user_from_request(self, user_id: str) -> Dict[str, str]:
        """Validate user_id and return user info for new unified auth system."""
        if not user_id:
            raise HTTPException(status_code=422, detail="Missing user_id")

        # Construct user_info dict compatible with existing services
        user_info = {
            'spotify_user_id': user_id,
            'user_id': user_id
        }
        
        return user_info

    async def get_access_token_for_user(self, user_id: str) -> Optional[str]:
        """Get access token for user_id (unified auth system)."""
        try:
            return await self.auth_service.get_access_token_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Failed to get access token for user {user_id}: {e}")
            return None

auth_middleware = AuthMiddleware()
