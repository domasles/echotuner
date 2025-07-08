"""
Auth middleware for FastAPI.
Handles user authentication and session validation.
"""

import logging

from fastapi import HTTPException, Request
from typing import Optional, Dict

from core.singleton import SingletonServiceBase

from services.auth_service import auth_service

logger = logging.getLogger(__name__)

class AuthMiddleware(SingletonServiceBase):
    """Middleware for validating user sessions and managing authentication."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the AuthMiddleware with the AuthService."""

        self.auth_service = auth_service
        self._log_initialization("Auth middleware initialized successfully", logger)

    async def validate_session_from_headers(self, request: Request) -> Dict[str, str]:
        session_id = request.headers.get('session_id')
        device_id = request.headers.get('device_id')

        if not session_id or not device_id:
            raise HTTPException(status_code=422, detail="Missing session_id or device_id headers")

        user_info = await self.auth_service.validate_session_and_get_user(session_id, device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return user_info

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

auth_middleware = AuthMiddleware()
