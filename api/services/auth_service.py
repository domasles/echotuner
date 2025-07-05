"""
Auth service.
Manages Spotify OAuth authentication, user sessions, and device registration.
"""

import logging
import secrets
import spotipy
import uuid

from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict

from core.singleton import SingletonServiceBase

from config.app_constants import AppConstants
from config.settings import settings

from services.database_service import db_service

logger = logging.getLogger(__name__)

class AuthService(SingletonServiceBase):
    """Service for managing Spotify OAuth authentication and user sessions."""

    def __init__(self):
        super().__init__()
    
    def _setup_service(self):
        """Initialize the AuthService."""

        self.db_path = AppConstants.DATABASE_FILENAME
        self.spotify_oauth = None

        self._initialize_spotify_oauth()

        if not settings.DEMO:
            self._cleanup_demo_accounts()
        
        self._log_initialization("Auth service initialized successfully", logger)

    def _initialize_spotify_oauth(self):
        """Initialize Spotify OAuth configuration"""

        try:
            if not all([settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, settings.SPOTIFY_REDIRECT_URI]):
                logger.warning("Spotify OAuth credentials not configured")
                return

            self.spotify_oauth = SpotifyOAuth(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                scope="user-read-private user-read-email user-follow-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
                show_dialog=True
            )

            logger.info("Spotify OAuth initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Spotify OAuth: {e}")

    def generate_auth_url(self, device_id: str, platform: str) -> tuple[str, str]:
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
            raise

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

            spotify = spotipy.Spotify(auth=token_info['access_token'])
            user_info = spotify.current_user()
            
            session_id = str(uuid.uuid4())
            device_id = device_info['device_id']  # Use the device_id from auth state
            
            if settings.DEMO:
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
            # Handle session cleanup based on account type being created
            existing_sessions = await db_service.get_sessions_by_device(device_id)
            for session in existing_sessions:
                existing_account_type = session.get('account_type', 'normal')
                
                # If creating demo session, only remove demo sessions (keep normal ones)
                if account_type == "demo" and existing_account_type == "demo":
                    await db_service.invalidate_session(session['session_id'])
                
                # If creating normal session, only remove normal sessions (keep demo ones)
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
            raise

    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate if session exists and belongs to device"""

        try:
            return await db_service.validate_session(session_id, device_id)

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    async def get_session_by_device(self, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device (for desktop polling)"""

        try:
            return await db_service.get_session_by_device(device_id)

        except Exception as e:
            logger.error(f"Get session by device error: {e}")
            return None

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

            logger.info(f"Registered new device: {device_id} on {platform}")
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

            logger.info(f"Auto-registered device: {device_id} on {platform}")
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

            # Block access when account type doesn't match API mode
            if settings.DEMO and account_type == 'normal':
                return None

            if not settings.DEMO and account_type == 'demo':
                return None

            if stored_device_id != device_id:
                return None

            if datetime.now().timestamp() > expires_at:
                await db_service.invalidate_session(session_id)
                return None

            await db_service.update_session_last_used(session_id)

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

                        await db_service.update_session_token(session_id, new_access_token, new_expires_at)
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

    async def get_user_from_session(self, session_id: str) -> Optional[Dict]:
        """Get user information from session ID."""

        try:
            session_info = await db_service.get_session_info(session_id)

            if not session_info:
                return None

            return {
                'spotify_user_id': session_info['spotify_user_id'],
                'device_id': session_info['device_id']
            }

        except Exception as e:
            logger.error(f"Failed to get user from session: {e}")
            return None

    async def is_session_expired(self, session_id: str) -> bool:
        """Check if a session is expired"""

        try:
            session_info = await db_service.get_session_info(session_id)

            if not session_info:
                return True

            return datetime.now().timestamp() > session_info['expires_at']

        except Exception as e:
            logger.error(f"Error checking session expiration: {e}")
            return True

    async def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration time"""

        try:
            new_expires_at = int((datetime.now() + timedelta(hours=hours)).timestamp())
            return await db_service.update_session_expiration(session_id, new_expires_at)

        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False

    async def revoke_all_user_sessions(self, spotify_user_id: str) -> bool:
        """Revoke all sessions for a specific user"""

        try:
            return await db_service.revoke_user_sessions(spotify_user_id)

        except Exception as e:
            logger.error(f"Error revoking user sessions: {e}")
            return False

    async def get_active_sessions_count(self, spotify_user_id: str) -> int:
        """Get count of active sessions for a user"""

        try:
            return await db_service.get_user_active_sessions_count(spotify_user_id)

        except Exception as e:
            logger.error(f"Error getting active sessions count: {e}")
            return 0

    async def get_account_type(self, session_id: str) -> Optional[str]:
        """Get account type for a session"""

        try:
            session_info = await db_service.get_session_info(session_id)

            if not session_info:
                return None

            return session_info.get('account_type', 'normal')

        except Exception as e:
            logger.error(f"Failed to get account type: {e}")
            return None

    async def is_session_compatible_with_mode(self, session_id: str) -> bool:
        """Check if session account type is compatible with current server mode"""
        
        try:
            session_info = await db_service.get_session_info(session_id)
            if not session_info:
                return False
                
            account_type = session_info.get('account_type', 'normal')
            current_mode_demo = settings.DEMO
            
            # Demo mode: only allow demo accounts
            if current_mode_demo and account_type != 'demo':
                logger.info(f"Session {session_id[:8]}... rejected: normal account in demo mode")
                return False
                
            # Normal mode: only allow normal accounts  
            if not current_mode_demo and account_type == 'demo':
                logger.info(f"Session {session_id[:8]}... rejected: demo account in normal mode")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Mode compatibility check failed: {e}")
            return False

    async def invalidate_device_completely(self, device_id: str):
        """Completely invalidate all sessions and data for a device"""
        
        try:
            # Get all sessions for this device
            sessions = await db_service.get_all_sessions_for_device(device_id)
            
            # Check if any sessions are demo accounts
            demo_sessions = [s for s in sessions if s.get('account_type') == 'demo']
            
            # Invalidate each session
            for session in sessions:
                session_id = session['session_id']
                await db_service.invalidate_session(session_id)
                logger.info(f"Invalidated session {session_id[:8]}... for device {device_id[:8]}...")
            
            # If there were demo sessions, delete demo account data
            if demo_sessions:
                await self._delete_demo_account_data(device_id, demo_sessions)
                
            # Clear any device-specific auth states
            await db_service.cleanup_device_auth_states(device_id)
            
            # For normal accounts: Rate limits are shared across devices by spotify_user_id, so don't clear them
            # For demo accounts: Rate limits are per device, but we don't clear them to prevent abuse
            # (Users would have to re-enter context anyway, so the rate limit protection is still valuable)
            
            logger.info(f"Completely invalidated device {device_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to completely invalidate device: {e}")

    async def _delete_demo_account_data(self, device_id: str, demo_sessions: list):
        """Delete all demo account data for a specific device"""
        try:
            # Delete demo user personality
            demo_user_id = f"demo_user_{device_id}"
            await db_service.execute_query(
                "DELETE FROM user_personalities WHERE user_id = ?",
                (demo_user_id,)
            )
            
            # Delete playlist drafts for demo sessions
            if demo_sessions:
                session_ids = [session['session_id'] for session in demo_sessions]
                placeholders = ','.join(['?' for _ in session_ids])
                await db_service.execute_query(
                    f"DELETE FROM playlist_drafts WHERE session_id IN ({placeholders})",
                    session_ids
                )
            
            logger.info(f"Deleted demo account data for device {device_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to delete demo account data: {e}")

    def _cleanup_demo_accounts(self):
        """Remove all demo accounts and related data when starting in normal mode"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_cleanup_demo_accounts())
        except Exception as e:
            logger.error(f"Failed to cleanup demo accounts: {e}")

    async def _async_cleanup_demo_accounts(self):
        """Async cleanup of demo accounts"""
        try:
            # First get all demo session IDs before deleting them
            demo_sessions = await db_service.fetch_all(
                "SELECT session_id FROM auth_sessions WHERE account_type = 'demo'"
            )
            
            # Delete demo playlist drafts (these use session_id from demo sessions)
            if demo_sessions:
                session_ids = [session['session_id'] for session in demo_sessions]
                placeholders = ','.join(['?' for _ in session_ids])
                await db_service.execute_query(
                    f"DELETE FROM playlist_drafts WHERE session_id IN ({placeholders})",
                    session_ids
                )
            
            # Delete demo sessions
            await db_service.execute_query(
                "DELETE FROM auth_sessions WHERE account_type = 'demo'"
            )
            
            # Delete demo user personalities (these use user_id like 'demo_user_deviceid')
            await db_service.execute_query(
                "DELETE FROM user_personalities WHERE user_id LIKE 'demo_user_%'"
            )
            
            logger.info("Cleaned up demo accounts for normal mode")
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

auth_service = AuthService()
