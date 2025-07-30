"""
OAuth Service Manager.
Manages OAuth providers and authentication flow.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from infrastructure.singleton import SingletonServiceBase
from domain.config.settings import settings
from infrastructure.database.repository import repository
from infrastructure.database.models import AuthSession, UserAccount, OwnerSpotifyCredentials, AuthState

from .spotify import SpotifyOAuthProvider
from .google import GoogleOAuthProvider

logger = logging.getLogger(__name__)

class OAuthService(SingletonServiceBase):
    """OAuth service for managing authentication providers."""
    
    def __init__(self):
        super().__init__()
    
    async def _setup_service(self):
        """Initialize OAuth providers."""
        
        # Initialize Spotify provider
        self.spotify_provider = SpotifyOAuthProvider(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI
        )
        
        # Initialize Google provider
        self.google_provider = GoogleOAuthProvider(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
    
    def get_auth_url(self, provider: str, appid: str = None) -> str:
        """Get OAuth authorization URL for the specified provider."""
        
        if provider == 'spotify':
            return self.spotify_provider.get_auth_url(state=appid)
        elif provider == 'google':
            return self.google_provider.get_auth_url(state=appid)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def handle_spotify_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle Spotify OAuth callback."""
        
        user_data = await self.spotify_provider.handle_callback(code, state)
        
        # Create user_id in format spotify_{id}
        user_id = f"spotify_{user_data['provider_user_id']}"
        
        # Store/update user account
        await self._store_user_account(user_id, user_data)
        
        # Update auth session if appid provided
        if state:
            await self._update_auth_session(state, user_id)
        
        return {'user_id': user_id, 'user_data': user_data}
    
    async def handle_google_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle Google OAuth callback."""
        
        user_data = await self.google_provider.handle_callback(code, state)
        
        # Create user_id in format google_{id}
        user_id = f"google_{user_data['provider_user_id']}"
        
        # Store/update user account (no tokens in shared mode)
        await self._store_user_account(user_id, user_data, store_tokens=False)
        
        # Update auth session if appid provided
        if state:
            await self._update_auth_session(state, user_id)
        
        return {'user_id': user_id, 'user_data': user_data}
    
    async def store_owner_credentials(self, code: str) -> Dict[str, Any]:
        """Store owner Spotify credentials for shared mode."""
        
        user_data = await self.spotify_provider.handle_callback(code)
        
        # Calculate expiry
        expires_at = None
        if user_data.get('expires_in'):
            expires_at = datetime.utcnow() + timedelta(seconds=user_data['expires_in'])
        
        # Store owner credentials
        owner_creds_data = {
            "id": "owner",
            "access_token": user_data['access_token'],
            "refresh_token": user_data['refresh_token'],
            "spotify_user_id": user_data['provider_user_id'],
            "expires_at": expires_at
        }
        
        await repository.create(OwnerSpotifyCredentials, owner_creds_data)
        
        logger.info("Owner Spotify credentials stored successfully")
        return user_data
    
    async def get_owner_credentials(self) -> Optional[OwnerSpotifyCredentials]:
        """Get owner Spotify credentials."""
        
        return await repository.get_by_id(OwnerSpotifyCredentials, "owner")
    
    async def get_access_token(self, user_id: str) -> Optional[str]:
        """Get access token for user. In shared mode, returns owner's token."""
        
        if settings.SHARED:
            # In shared mode, use owner's credentials for all users
            owner_creds = await self.get_owner_credentials()
            if owner_creds:
                # Check if token needs refresh
                if self._is_token_expired(owner_creds):
                    # Refresh owner token
                    refreshed_creds = await self._refresh_owner_token(owner_creds)
                    if refreshed_creds:
                        return refreshed_creds.access_token
                    return None
                return owner_creds.access_token
            return None
        else:
            # In normal mode, get user's personal token
            user = await repository.get_by_field(UserAccount, 'user_id', user_id)
            if user and user.access_token:
                # Check if token needs refresh (if refresh logic is implemented)
                return user.access_token
            return None
    
    def _is_token_expired(self, creds: OwnerSpotifyCredentials) -> bool:
        """Check if token is expired."""
        if not creds.expires_at:
            return False
        return datetime.utcnow() >= creds.expires_at
    
    async def _refresh_owner_token(self, creds: OwnerSpotifyCredentials) -> Optional[OwnerSpotifyCredentials]:
        """Refresh owner's access token."""
        try:
            if not creds.refresh_token:
                logger.error("No refresh token available for owner")
                return None
            
            # Use Spotify provider to refresh token
            refreshed_data = await self.spotify_provider.refresh_token(creds.refresh_token)
            
            if refreshed_data:
                # Update owner credentials
                update_data = {
                    "access_token": refreshed_data.get('access_token'),
                }
                if refreshed_data.get('expires_in'):
                    update_data["expires_at"] = datetime.utcnow() + timedelta(seconds=refreshed_data['expires_in'])
                if refreshed_data.get('refresh_token'):
                    update_data["refresh_token"] = refreshed_data['refresh_token']
                
                await repository.update_by_conditions(OwnerSpotifyCredentials, {"id": "owner"}, update_data)
                
                # Return updated credentials
                return await self.get_owner_credentials()
            
        except Exception as e:
            logger.error(f"Failed to refresh owner token: {e}")
        
        return None
    
    async def create_auth_session(self, appid: str) -> None:
        """Create new auth session for polling."""
        
        session_data = {"appid": appid}
        await repository.create(AuthSession, session_data)
    
    async def check_auth_session(self, appid: str) -> Optional[str]:
        """Check auth session status and return user_id if completed."""
        
        session = await repository.get_by_field(AuthSession, 'appid', appid)
        
        if not session:
            return None
        
        if session.userid:
            # Authentication completed, cleanup session
            await repository.delete_by_conditions(AuthSession, {"appid": session.appid})
            return session.userid
        
        return None  # Still waiting
    
    async def _store_user_account(self, user_id: str, user_data: Dict[str, Any], store_tokens: bool = True) -> None:
        """Store or update user account."""
        
        # Check if user exists
        user_account = await repository.get_by_field(UserAccount, 'user_id', user_id)
        
        if not user_account:
            # Create new user account data
            user_data_for_create = {
                "user_id": user_id,
                "provider": user_data['provider'],
                "provider_user_id": user_data['provider_user_id']
            }
            
            # Add tokens if storing them (Normal mode only)
            if store_tokens and user_data.get('access_token'):
                user_data_for_create["access_token"] = user_data['access_token']
                user_data_for_create["refresh_token"] = user_data.get('refresh_token')
                
                if user_data.get('expires_in'):
                    user_data_for_create["expires_at"] = datetime.utcnow() + timedelta(seconds=user_data['expires_in'])
            
            await repository.create(UserAccount, user_data_for_create)
        else:
            # Update existing user account if storing tokens
            if store_tokens and user_data.get('access_token'):
                update_data = {
                    "access_token": user_data['access_token'],
                    "refresh_token": user_data.get('refresh_token')
                }
                
                if user_data.get('expires_in'):
                    update_data["expires_at"] = datetime.utcnow() + timedelta(seconds=user_data['expires_in'])
                
                await repository.update_by_conditions(UserAccount, {"user_id": user_id}, update_data)
    
    async def _update_auth_session(self, appid: str, user_id: str) -> None:
        """Update auth session with user_id."""
        
        session = await repository.get_by_field(AuthSession, 'appid', appid)
        
        if session:
            update_data = {"userid": user_id}
            await repository.update_by_conditions(AuthSession, {"appid": appid}, update_data)
    
    async def store_auth_state(self, state: str, appid: str, platform: str) -> bool:
        """Store auth state for validation."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            # Check if state already exists and delete it first
            existing_state = await repository.get_by_field(AuthState, 'state', state)
            if existing_state:
                await repository.delete(AuthState, existing_state.state, 'state')
            
            auth_state_data = {
                'state': state,
                'appid': appid,
                'platform': platform,
                'created_at': int(datetime.utcnow().timestamp()),
                'expires_at': int(expires_at.timestamp())
            }
            
            await repository.create(AuthState, auth_state_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store auth state: {e}")
            return False

    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return app info."""
        try:
            auth_state = await repository.get_by_field(AuthState, 'state', state)
            if not auth_state:
                logger.warning(f"Auth state not found: {state}")
                return None
            
            # Check if expired
            if auth_state.expires_at < datetime.utcnow().timestamp():
                logger.warning(f"Auth state expired: {state}")
                await repository.delete(AuthState, auth_state.state, 'state')
                return None
            
            # Clean up after successful validation
            await repository.delete(AuthState, auth_state.state, 'state')
            
            return {
                'appid': auth_state.appid,
                'platform': auth_state.platform
            }
            
        except Exception as e:
            logger.error(f"Failed to validate auth state: {e}")
            return None

    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return True

    async def get_access_token_by_user_id(self, user_id: str) -> Optional[str]:
        """Get access token by user_id (unified auth system)."""
        try:
            # In shared mode, use owner credentials
            if settings.SHARED:
                owner_creds = await self.get_owner_credentials()
                if not owner_creds:
                    logger.error("No owner credentials found in shared mode")
                    return None
                
                # Check if token is expired and refresh if needed
                now = datetime.now()
                if self._is_token_expired(owner_creds):
                    refreshed_creds = await self._refresh_owner_token(owner_creds)
                    if refreshed_creds:
                        return refreshed_creds.access_token
                    else:
                        logger.error("Failed to refresh owner token")
                        return None
                
                return owner_creds.access_token
            
            else:
                # Normal mode - get user's individual access token
                return await self.get_access_token(user_id)
                
        except Exception as e:
            logger.error(f"Failed to get access token for user {user_id}: {e}")
            return None

oauth_service = OAuthService()
