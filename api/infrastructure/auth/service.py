"""
OAuth Service Manager.
Manages OAuth providers and authentication flow.
"""

import logging
import asyncio

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
        self._cleanup_task: Optional[asyncio.Task] = None
    
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

        # Start background cleanup task for orphaned auth sessions
        self._cleanup_task = asyncio.create_task(self._periodic_session_cleanup())
        logger.info("Started background auth session cleanup task")
    
    def get_auth_url(self, provider: str, app_id: str = None) -> str:
        """Get OAuth authorization URL for the specified provider."""
        
        if provider == 'spotify':
            return self.spotify_provider.get_auth_url(state=app_id)
        elif provider == 'google':
            return self.google_provider.get_auth_url(state=app_id)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def handle_spotify_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle Spotify OAuth callback."""
        
        user_data = await self.spotify_provider.handle_callback(code, state)
        
        # Create user_id in format spotify_{id}
        user_id = f"spotify_{user_data['provider_user_id']}"
        
        # Store/update user account
        await self._store_user_account(user_id, user_data)
        
        # Update auth session if app_id provided
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
        
        # Update auth session if app_id provided
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
    
    async def create_auth_session(self, app_id: str) -> None:
        """Create new auth session for polling."""
        
        session_data = {"app_id": app_id}
        await repository.create(AuthSession, session_data)
    
    async def check_auth_session(self, app_id: str) -> Optional[str]:
        """Check auth session status and return user_id if completed."""
        
        session = await repository.get_by_field(AuthSession, 'app_id', app_id)
        
        if not session:
            return None
        
        # Check if session has expired (10 minute timeout)
        max_age = timedelta(minutes=10)
        if datetime.utcnow() - session.created_at > max_age:
            logger.debug(f"Auth session {app_id} expired, deleting")
            await repository.delete_by_conditions(AuthSession, {"app_id": app_id})
            return None
        
        if session.user_id:
            # Authentication completed, cleanup session
            await repository.delete_by_conditions(AuthSession, {"app_id": session.app_id})
            return session.user_id
        
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

            if user_data.get('user_info'):
                user_info = user_data['user_info']

                if user_data['provider'] == 'spotify':
                    user_data_for_create["display_name"] = user_info.get('display_name')
                elif user_data['provider'] == 'google':
                    user_data_for_create["display_name"] = user_info.get('name')
            
            # Add tokens if storing them (Normal mode only)
            if store_tokens and user_data.get('access_token'):
                user_data_for_create["access_token"] = user_data['access_token']
                user_data_for_create["refresh_token"] = user_data.get('refresh_token')
                
                if user_data.get('expires_in'):
                    user_data_for_create["expires_at"] = datetime.utcnow() + timedelta(seconds=user_data['expires_in'])
            
            await repository.create(UserAccount, user_data_for_create)
        else:
            update_data = {}

            if user_data.get('user_info'):
                user_info = user_data['user_info']

                if user_data['provider'] == 'spotify':
                    update_data["display_name"] = user_info.get('display_name')
                elif user_data['provider'] == 'google':
                    update_data["display_name"] = user_info.get('name')  # Google uses 'name' field
            
            # Update tokens if storing them
            if store_tokens and user_data.get('access_token'):
                update_data["access_token"] = user_data['access_token']
                update_data["refresh_token"] = user_data.get('refresh_token')
                
                if user_data.get('expires_in'):
                    update_data["expires_at"] = datetime.utcnow() + timedelta(seconds=user_data['expires_in'])
            
            if update_data:
                await repository.update_by_conditions(UserAccount, {"user_id": user_id}, update_data)
    
    async def _update_auth_session(self, app_id: str, user_id: str) -> None:
        """Update auth session with user_id."""
        
        session = await repository.get_by_field(AuthSession, 'app_id', app_id)
        
        if session:
            update_data = {"user_id": user_id}
            await repository.update_by_conditions(AuthSession, {"app_id": app_id}, update_data)
    
    async def store_auth_state(self, state: str, app_id: str, platform: str) -> bool:
        """Store auth state for validation."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            # Check if state already exists and delete it first
            existing_state = await repository.get_by_field(AuthState, 'state', state)
            if existing_state:
                await repository.delete(AuthState, existing_state.state, 'state')
            
            auth_state_data = {
                'state': state,
                'app_id': app_id,
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
                'app_id': auth_state.app_id,
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
    
    async def _periodic_session_cleanup(self):
        """Background task to cleanup expired auth sessions."""
        
        while True:
            try:
                await asyncio.sleep(int((settings.AUTH_UUID_CLEANUP_MINUTES / 2) * 60))
                await self._cleanup_expired_sessions(settings.AUTH_UUID_CLEANUP_MINUTES)
            except asyncio.CancelledError:
                logger.info("Auth session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
    
    async def _cleanup_expired_sessions(self, max_age_minutes: int = 10):
        """Delete auth sessions older than max_age_minutes with no user_id."""
        
        try:
            expiry_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            
            # Get all expired orphaned sessions
            all_sessions = await repository.list_all(AuthSession)
            deleted_count = 0
            
            for session in all_sessions:
                # Delete if: no user_id AND older than max_age
                if not session.user_id and session.created_at < expiry_time:
                    await repository.delete_by_conditions(AuthSession, {"app_id": session.app_id})
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired auth session(s)")
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
    
    async def cleanup(self):
        """Cleanup service resources."""
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("OAuth service cleaned up")

oauth_service = OAuthService()
