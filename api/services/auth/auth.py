"""
Auth service.
Manages Spotify OAuth authentication, user sessions, and device registration.
"""

import asyncio
import logging
import secrets
import spotipy
import uuid

from spotipy.cache_handler import CacheFileHandler
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict

from core.singleton import SingletonServiceBase
from config.settings import settings

from core.validation.validators import UniversalValidator

from services.database.database import db_service
from core.service.decorators import service_bool_operation, service_optional_operation

from config.app_constants import app_constants

logger = logging.getLogger(__name__)

class AuthService(SingletonServiceBase):
    """Service for managing Spotify OAuth authentication and user sessions."""

    def __init__(self):
        super().__init__()
        # Demo mode owner token storage
        self._demo_owner_token_info = None
        self._demo_owner_lock = asyncio.Lock()

    def _setup_service(self):
        """Initialize the AuthService."""

        self.spotify_oauth = None
        self._initialize_spotify_oauth()

        # Note: Demo cleanup is deferred to initialize() method 
        # to ensure database service is available
        self._log_initialization("Auth service initialized successfully", logger)

    async def initialize(self):
        """Initialize the auth service with async operations"""
        try:
            # Only cleanup demo accounts if not in demo mode and database is available
            if not settings.DEMO and hasattr(self, '_setup_service'):
                await self._async_cleanup_demo_accounts()
            
            # In demo mode, try to load existing owner token
            if settings.DEMO:
                await self._load_demo_owner_token()
            
            logger.info("Auth service async initialization completed")
            
        except Exception as e:
            logger.warning(f"Auth service initialization warning: {e}")
            # Don't fail initialization for cleanup issues

    def _initialize_spotify_oauth(self):
        """Initialize Spotify OAuth configuration"""

        try:
            if not all([settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, settings.SPOTIFY_REDIRECT_URI]):
                logger.warning("Spotify OAuth credentials not configured")
                return
            
            cache_handler = CacheFileHandler(cache_path=app_constants.SPOTIFY_TOKEN_CACHE_FILEPATH)

            self.spotify_oauth = SpotifyOAuth(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                scope="user-read-private user-read-email user-follow-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
                cache_handler=cache_handler,
                show_dialog=True
            )

            logger.info("Spotify OAuth initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Spotify OAuth: {e}")

    def generate_auth_url(self) -> tuple[str, str]:
        """Generate Spotify OAuth URL and state"""

        if not self.spotify_oauth:
            raise Exception("Spotify OAuth not configured")

        state = secrets.token_urlsafe(32)
        auth_url = self.spotify_oauth.get_authorize_url(state=state)

        return auth_url, state

    async def store_auth_state(self, state: str, device_id: str, platform: str):
        """Store auth state for validation"""

        try:
            expires_at = int((datetime.now() + timedelta(minutes=10)).timestamp())
            return await db_service.store_auth_state(state, device_id, platform, expires_at)

        except Exception as e:
            logger.error(f"Failed to store auth state: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return device info"""

        try:
            return await db_service.validate_auth_state(state)

        except Exception as e:
            logger.error(f"Failed to validate auth state: {e}")
            return None

    async def handle_spotify_callback(self, code: str, state: str, device_info: Dict) -> Optional[str]:
        """Handle Spotify OAuth callback"""

        try:
            if not self.spotify_oauth:
                logger.error("Spotify OAuth not initialized")
                return None

            token_info = self.spotify_oauth.get_access_token(code)

            if not token_info:
                logger.error("Failed to get access token from Spotify")
                return None

            spotify = spotipy.Spotify(auth_manager=self.spotify_oauth)
            user_info = spotify.current_user()
            
            session_id = str(uuid.uuid4())
            device_id = device_info['device_id']

            if settings.DEMO:
                # In demo mode, store the owner's token on first successful login
                async with self._demo_owner_lock:
                    if self._demo_owner_token_info is None:
                        logger.info("Storing owner's Spotify credentials for demo mode")
                        self._demo_owner_token_info = {
                            'access_token': token_info['access_token'],
                            'refresh_token': token_info.get('refresh_token'),
                            'expires_at': int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp()),
                            'spotify_user_id': user_info['id']
                        }
                        # Store to database for persistence
                        await self._store_demo_owner_token()
                
                demo_user_id = f"demo_user_{device_id}"
                account_type = "demo"

            else:
                demo_user_id = user_info['id']
                account_type = "normal"

            await self.create_session(
                session_id=session_id,
                device_id=device_id,
                platform=device_info['platform'],
                spotify_user_id=demo_user_id,
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                expires_at=int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp()),
                account_type=account_type
            )

            return session_id

        except Exception as e:
            logger.error(f"Failed to handle Spotify callback: {e}")
            return None

    async def create_session(self, session_id: str, device_id: str, platform: str, spotify_user_id: str, access_token: str, refresh_token: Optional[str], expires_at: int, account_type: str = "normal"):
        """Create a new auth session"""

        try:
            existing_sessions = await db_service.get_sessions_by_device(device_id)

            for session in existing_sessions:
                existing_account_type = session.get('account_type', 'normal')

                if account_type == "demo" and existing_account_type == "demo":
                    await db_service.invalidate_session(session['session_id'])

                elif account_type == "normal" and existing_account_type == "normal":
                    await db_service.invalidate_session(session['session_id'])

            now = int(datetime.now().timestamp())

            session_data = {
                'session_id': session_id,
                'device_id': device_id,
                'platform': platform,
                'spotify_user_id': spotify_user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'created_at': now,
                'last_used_at': now,
                'account_type': account_type
            }

            success = await db_service.create_session(session_data)

            if not success:
                raise Exception("Failed to create session in database")

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    @service_bool_operation()
    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate if session exists and belongs to device"""
        return await db_service.validate_session(session_id, device_id)

    @service_optional_operation()
    async def get_session_by_device(self, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device (for desktop polling)"""
        return await db_service.get_session_by_device(device_id)

    async def invalidate_session(self, session_id: str):
        """Invalidate a session"""

        try:
            await db_service.invalidate_session(session_id)

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions and states"""

        try:
            await db_service.cleanup_expired_sessions()

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

    def is_ready(self) -> bool:
        """Check if auth service is ready for use"""

        return self.spotify_oauth is not None and all([settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, settings.SPOTIFY_REDIRECT_URI])

    async def register_device(self, platform: str, app_version: Optional[str] = None, device_fingerprint: Optional[str] = None) -> tuple[str, int]:
        """Register a new device and return server-generated UUID"""

        try:
            device_id = str(uuid.uuid4())
            registration_timestamp = int(datetime.now().timestamp())

            device_data = {
                'device_id': device_id,
                'platform': platform,
                'app_version': app_version,
                'device_fingerprint': device_fingerprint,
                'registration_timestamp': registration_timestamp,
                'last_seen_timestamp': registration_timestamp,
                'is_active': 1
            }

            success = await db_service.register_device(device_data)

            if not success:
                raise Exception("Device registration failed")

            logger.debug(f"Registered new device: {device_id} on {platform}")
            return device_id, registration_timestamp

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            raise Exception("Device registration failed")

    async def register_device_with_id(self, device_id: str, platform: str, app_version: Optional[str] = None, device_fingerprint: Optional[str] = None) -> int:
        """Register a device with a specific ID (for auto-registration)"""

        try:
            registration_timestamp = int(datetime.now().timestamp())

            device_data = {
                'device_id': device_id,
                'platform': platform,
                'app_version': app_version,
                'device_fingerprint': device_fingerprint,
                'registration_timestamp': registration_timestamp,
                'last_seen_timestamp': registration_timestamp,
                'is_active': 1
            }

            success = await db_service.register_device(device_data)

            if not success:
                raise Exception("Device registration failed")

            logger.debug(f"Auto-registered device: {device_id} on {platform}")
            return registration_timestamp

        except Exception as e:
            logger.error(f"Failed to register device with ID: {e}")
            raise Exception("Device registration failed")

    async def validate_device(self, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate that device_id was issued by server and is active"""

        try:
            return await db_service.validate_device(device_id, update_last_seen)

        except Exception as e:
            logger.error(f"Device validation failed: {e}")
            return False

    async def validate_session_and_get_user(self, session_id: str, device_id: str) -> Optional[Dict[str, str]]:
        """Validate session and return user info if valid"""

        try:
            session_info = await db_service.get_session_info(session_id)

            if not session_info:
                return None

            stored_device_id = session_info['device_id']
            expires_at = session_info['expires_at']
            spotify_user_id = session_info['spotify_user_id']
            account_type = session_info.get('account_type', 'normal')

            if settings.DEMO and account_type == 'normal':
                return None

            if not settings.DEMO and account_type == 'demo':
                return None

            if stored_device_id != device_id:
                return None

            if datetime.now().timestamp() > expires_at:
                await db_service.invalidate_session(session_id)
                return None

            await db_service.update_session(session_id, update_last_used=True)

            return {
                "spotify_user_id": spotify_user_id,
                "device_id": device_id,
                "account_type": account_type
            }

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def get_access_token(self, session_id: str) -> Optional[str]:
        """Get access token for a session."""

        try:
            # In demo mode, always use owner's token regardless of session
            if settings.DEMO:
                async with self._demo_owner_lock:
                    if self._demo_owner_token_info:
                        # Check if owner token is expired and refresh if needed
                        if datetime.now().timestamp() > self._demo_owner_token_info['expires_at']:
                            if self._demo_owner_token_info.get('refresh_token') and self.spotify_oauth:
                                try:
                                    token_info = self.spotify_oauth.refresh_access_token(self._demo_owner_token_info['refresh_token'])
                                    self._demo_owner_token_info.update({
                                        'access_token': token_info['access_token'],
                                        'expires_at': int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp())
                                    })
                                    await self._store_demo_owner_token()
                                    logger.debug("Refreshed demo owner token")
                                    return token_info['access_token']
                                except Exception as e:
                                    logger.error(f"Failed to refresh demo owner token: {e}")
                                    return None
                            else:
                                logger.warning("Demo owner token expired and no refresh token available")
                                return None
                        
                        return self._demo_owner_token_info['access_token']
                    else:
                        logger.warning("No demo owner token available")
                        return None

            # Normal mode - use session-specific token
            session_info = await db_service.get_session_info(session_id)

            if not session_info:
                return None

            access_token = session_info['access_token']
            expires_at = session_info['expires_at']
            refresh_token = session_info['refresh_token']

            if datetime.now().timestamp() > expires_at:
                if refresh_token and self.spotify_oauth:
                    try:
                        token_info = self.spotify_oauth.refresh_access_token(refresh_token)
                        new_access_token = token_info['access_token']
                        new_expires_at = int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp())

                        await db_service.update_session(session_id, access_token=new_access_token, expires_at=new_expires_at)
                        return new_access_token

                    except Exception as e:
                        logger.error(f"Failed to refresh token: {e}")
                        return None

                else:
                    return None

            return access_token

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None

    @service_optional_operation()
    async def get_user_from_session(self, session_id: str) -> Optional[Dict]:
        """Get user information from session ID."""
        session_info = await db_service.get_session_info(session_id)

        if not session_info:
            return None

        return {
            'spotify_user_id': session_info['spotify_user_id'],
            'device_id': session_info['device_id']
        }

    @service_bool_operation()
    async def is_session_expired(self, session_id: str) -> bool:
        """Check if a session is expired"""
        session_info = await db_service.get_session_info(session_id)

        if not session_info:
            return True

        return datetime.now().timestamp() > session_info['expires_at']

    @service_bool_operation()
    async def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration time"""
        new_expires_at = int((datetime.now() + timedelta(hours=hours)).timestamp())
        return await db_service.update_session(session_id, expires_at=new_expires_at)

    @service_bool_operation()
    async def revoke_all_user_sessions(self, spotify_user_id: str) -> bool:
        """Revoke all sessions for a specific user"""
        return await db_service.revoke_user_sessions(spotify_user_id)

    async def get_active_sessions_count(self, spotify_user_id: str) -> int:
        """Get count of active sessions for a user"""

        try:
            return await db_service.get_user_active_sessions_count(spotify_user_id)

        except Exception as e:
            logger.error(f"Error getting active sessions count: {e}")
            return 0

    @service_optional_operation()
    async def get_account_type(self, session_id: str) -> Optional[str]:
        """Get account type for a session"""
        session_info = await db_service.get_session_info(session_id)

        if not session_info:
            return None

        return session_info.get('account_type', 'normal')

    async def is_session_compatible_with_mode(self, session_id: str) -> bool:
        """Check if session account type is compatible with current server mode"""

        try:
            session_info = await db_service.get_session_info(session_id)
            if not session_info:
                return False

            account_type = session_info.get('account_type', 'normal')
            current_mode_demo = settings.DEMO

            if current_mode_demo and account_type != 'demo':
                logger.debug(f"Session {session_id[:8]}... rejected: normal account in demo mode")
                return False

            if not current_mode_demo and account_type == 'demo':
                logger.debug(f"Session {session_id[:8]}... rejected: demo account in normal mode")
                return False

            return True

        except Exception as e:
            logger.error(f"Mode compatibility check failed: {e}")
            return False

    async def invalidate_device_completely(self, device_id: str):
        """Completely invalidate all sessions and data for a device"""

        try:
            sessions = await db_service.get_all_sessions_for_device(device_id)
            demo_sessions = [s for s in sessions if s.get('account_type') == 'demo']

            for session in sessions:
                session_id = session['session_id']
                await db_service.invalidate_session(session_id)
                logger.debug(f"Invalidated session {session_id[:8]}... for device {device_id[:8]}...")

            if demo_sessions:
                await self._delete_demo_account_data(device_id, demo_sessions)

            await db_service.cleanup_device_auth_states(device_id)
            logger.debug(f"Completely invalidated device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to completely invalidate device: {e}")

    async def _delete_demo_account_data(self, device_id: str, demo_sessions: list):
        """Delete all demo account data for a specific device"""

        try:
            demo_user_id = f"demo_user_{device_id}"
            await db_service.delete_user_personality(demo_user_id)

            if demo_sessions:
                session_ids = [session['session_id'] for session in demo_sessions]
                await db_service.delete_playlist_drafts_by_sessions(session_ids)

            logger.debug(f"Deleted demo account data for device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to delete demo account data: {e}")

    def _cleanup_demo_accounts(self):
        """Remove all demo accounts and related data when starting in normal mode"""

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_cleanup_demo_accounts())

        except Exception as e:
            logger.error(f"Failed to cleanup demo accounts: {e}")

    async def _async_cleanup_demo_accounts(self):
        """Async cleanup of demo accounts"""
        try:
            demo_sessions = await db_service.get_sessions_by_account_type('demo')

            if demo_sessions:
                session_ids = [session['session_id'] for session in demo_sessions]
                await db_service.delete_playlist_drafts_by_sessions(session_ids)

            await db_service.delete_auth_sessions_by_account_type('demo')
            await db_service.delete_demo_user_personalities()
            
            # Clear demo owner token when switching to normal mode
            await db_service.clear_demo_owner_token()

            logger.debug("Cleaned up demo accounts for normal mode")

        except Exception as e:
            logger.error(f"Failed to cleanup demo accounts: {e}")

    async def create_demo_session(self, device_id: str, platform: str) -> str:
        """Create a demo session for the device"""

        session_id = str(uuid.uuid4())
        demo_user_id = f"demo_user_{device_id}"

        await self.create_session(
            session_id=session_id,
            device_id=device_id,
            platform=platform,
            spotify_user_id=demo_user_id,
            access_token="demo_token",
            refresh_token=None,
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
            account_type="demo"
        )

        return session_id

    async def _store_demo_owner_token(self):
        """Store demo owner token to database for persistence"""
        try:
            if self._demo_owner_token_info:
                await db_service.store_demo_owner_token(self._demo_owner_token_info)
        except Exception as e:
            logger.error(f"Failed to store demo owner token: {e}")

    async def _load_demo_owner_token(self):
        """Load demo owner token from database"""
        try:
            token_info = await db_service.get_demo_owner_token()
            if token_info:
                async with self._demo_owner_lock:
                    self._demo_owner_token_info = token_info
                    logger.info("Loaded existing demo owner token")
        except Exception as e:
            logger.warning(f"Failed to load demo owner token: {e}")

    def has_demo_owner_token(self) -> bool:
        """Check if demo mode has an owner token stored"""
        return settings.DEMO and self._demo_owner_token_info is not None

    async def create_demo_bypass_session(self, device_id: str, platform: str) -> str:
        """Create a demo session that bypasses OAuth (for subsequent users after owner)"""
        session_id = str(uuid.uuid4())
        demo_user_id = f"demo_user_{device_id}"

        # Use a dummy token since we'll use owner's token for actual API calls
        await self.create_session(
            session_id=session_id,
            device_id=device_id,
            platform=platform,
            spotify_user_id=demo_user_id,
            access_token="demo_bypass_token",
            refresh_token=None,
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
            account_type="demo"
        )

        return session_id
            
auth_service = AuthService()
