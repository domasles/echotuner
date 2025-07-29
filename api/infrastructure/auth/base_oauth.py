"""
Base OAuth Provider Interface.
Defines common interface for OAuth providers (Spotify, Google).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseOAuthProvider(ABC):
    """Base class for OAuth providers."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    @abstractmethod
    def get_auth_url(self, state: str = None) -> str:
        """Generate OAuth authorization URL."""
        pass
    
    @abstractmethod
    async def handle_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle OAuth callback and return user data."""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name."""
        pass
