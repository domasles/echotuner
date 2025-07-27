"""
Clean Auth service - manages its own data operations via repository.
No dependency on monolithic database service.
"""

import asyncio
import logging
import secrets
import uuid
from spotipy.cache_handler import CacheFileHandler
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict, Any, List

from infrastructure.singleton import SingletonServiceBase
from infrastructure.config.settings import settings
from infrastructure.database import repository
from infrastructure.database.models import AuthState
from infrastructure.config.app_constants import app_constants

logger = logging.getLogger(__name__)

class AuthService(SingletonServiceBase):
    """Clean auth service managing its own data via repository."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the AuthService."""
        self.repo = repository
        self.spotify_oauth = None
        self._initialize_spotify_oauth()
        logger.info("Auth service initialized successfully")

    def _initialize_spotify_oauth(self):
        """Initialize Spotify OAuth with proper settings."""
        try:
            cache_handler = CacheFileHandler(cache_path=app_constants.SPOTIFY_CACHE_PATH)
            
            self.spotify_oauth = SpotifyOAuth(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                scope=app_constants.SPOTIFY_SCOPE,
                cache_handler=cache_handler,
                show_dialog=True
            )
            logger.info("Spotify OAuth initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify OAuth: {e}")

    async def initialize(self):
        """Initialize async components."""
            
        logger.info("Auth service async initialization completed")

    # AUTH STATE MANAGEMENT
    async def store_auth_state(self, state: str, appid: str, platform: str) -> bool:
        """Store auth state for validation."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            # Check if state already exists and delete it first
            existing_state = await self.repo.get_by_field(AuthState, 'state', state)
            if existing_state:
                await self.repo.delete(AuthState, existing_state.state, 'state')
            
            auth_state_data = {
                'state': state,
                'appid': appid,
                'platform': platform,
                'created_at': int(datetime.utcnow().timestamp()),
                'expires_at': int(expires_at.timestamp())
            }
            
            await self.repo.create(AuthState, auth_state_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store auth state: {e}")
            return False

    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return app info."""
        try:
            auth_state = await self.repo.get_by_field(AuthState, 'state', state)
            
            if not auth_state:
                return None
                
            # Check if expired
            if auth_state.expires_at < int(datetime.utcnow().timestamp()):
                await self.repo.delete(AuthState, auth_state.state, 'state')
                return None

            return {
                'appid': auth_state.appid,
                'platform': auth_state.platform
            }
            
        except Exception as e:
            logger.error(f"Failed to validate auth state: {e}")
            return None


    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return True  # Auth service is always ready since it uses repository pattern

    async def get_access_token_by_user_id(self, user_id: str) -> Optional[str]:
        """Get access token by user_id (unified auth system)."""
        try:
            from infrastructure.auth.oauth_service import oauth_service
            from datetime import datetime, timedelta
            
            # In shared mode, use owner credentials
            if settings.SHARED:
                owner_creds = await oauth_service.get_owner_credentials()
                if not owner_creds:
                    logger.error("No owner credentials found in shared mode")
                    return None
                
                # Check if token is expired and refresh if needed
                now = datetime.now()
                if owner_creds.expires_at and owner_creds.expires_at <= now:
                    logger.debug("Owner access token expired, refreshing...")
                    try:
                        # Refresh the token using Spotify provider
                        new_token_data = await oauth_service.spotify_provider.refresh_token(owner_creds.refresh_token)
                        
                        # Update owner credentials with new token
                        from infrastructure.database.repository import repository
                        from infrastructure.database.models.owner_credentials import OwnerSpotifyCredentials
                        from datetime import timedelta
                        
                        update_data = {
                            'access_token': new_token_data['access_token'],
                            'expires_at': datetime.now() + timedelta(seconds=new_token_data.get('expires_in', 3600)),
                            'updated_at': datetime.now()
                        }
                        
                        await repository.update(OwnerSpotifyCredentials, owner_creds.id, update_data)
                        logger.debug("Owner access token refreshed successfully")
                        return new_token_data['access_token']
                        
                    except Exception as e:
                        logger.error(f"Failed to refresh owner token: {e}")
                        return None
                else:
                    return owner_creds.access_token
            else:
                # In normal mode, get user's own token from UserAccount
                from infrastructure.database.repository import repository
                from infrastructure.database.models.auth import UserAccount
                
                user_account = await repository.get_by_field(UserAccount, 'user_id', user_id)
                if user_account and user_account.access_token:
                    # Token refresh for user accounts could be implemented here
                    return user_account.access_token
                return None
                    
        except Exception as e:
            logger.error(f"Failed to get access token for user {user_id}: {e}")
            return None

# Global service instance
auth_service = AuthService()
