"""
Service validation utilities for EchoTuner API.

This module provides common service validation patterns
to reduce code duplication across endpoints.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

from core.auth.middleware import auth_middleware
from services.ai.ai import ai_service
from services.playlist.spotify import spotify_playlist_service
from services.playlist.generator import playlist_generator_service
from services.playlist.draft import playlist_draft_service
from services.personality.personality import personality_service


class ServiceValidator:
    """Utility class for common service validation patterns."""
    
    @staticmethod
    async def validate_and_get_user_info(session_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and get user info with standardized error handling."""
        try:
            return await auth_middleware.validate_session_from_request(session_id, device_id)
        except Exception as e:
            logging.getLogger(__name__).error(f"Session validation failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    @staticmethod
    def check_service_availability(service_name: str, service_instance) -> None:
        """Check if a service is available and raise appropriate error if not."""
        if not service_instance.is_ready():
            raise HTTPException(status_code=503, detail=f"{service_name} service is unavailable")

    @staticmethod
    def check_ai_service() -> None:
        """Check AI service availability."""
        ServiceValidator.check_service_availability("AI", ai_service)
    
    @staticmethod
    def check_spotify_service() -> None:
        """Check Spotify service availability."""
        ServiceValidator.check_service_availability("Spotify", spotify_playlist_service)
    
    @staticmethod
    def check_playlist_generator_service() -> None:
        """Check playlist generator service availability."""
        ServiceValidator.check_service_availability("Playlist Generator", playlist_generator_service)
    
    @staticmethod
    def check_playlist_draft_service() -> None:
        """Check playlist draft service availability."""
        ServiceValidator.check_service_availability("Playlist Draft", playlist_draft_service)
    
    @staticmethod
    def check_personality_service() -> None:
        """Check personality service availability."""
        ServiceValidator.check_service_availability("Personality", personality_service)
