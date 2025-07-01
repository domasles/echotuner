"""Authentication service for Spotify OAuth and session management."""

import logging
import secrets
import spotipy
import uuid

from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict

from services.database_service import db_service
from core.singleton import SingletonServiceBase
from config.app_constants import AppConstants
from config.settings import settings

logger = logging.getLogger(__name__)

class AuthService(SingletonServiceBase):
    def _setup_service(self):
        """Initialize the AuthService."""

        self.db_path = AppConstants.DATABASE_FILENAME
        self.spotify_oauth = None

        self._initialize_spotify_oauth()
        self._log_initialization("Auth service initialized successfully", logger)

    def __init__(self):
        super().__init__()

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

    async def handle_spotify_callback(self, code: str, state: str) -> Optional[str]:
        """Handle Spotify OAuth callback and create session"""

        try:
            device_info = await self.validate_auth_state(state)

            if not device_info:
                logger.warning(f"Invalid or expired auth state: {state}")
                return None

            if not self.spotify_oauth:
                raise Exception("Spotify OAuth not configured")

            token_info = self.spotify_oauth.get_access_token(code)

            if not token_info:
                logger.error("Failed to get access token from Spotify")
                return None

            spotify = spotipy.Spotify(auth=token_info['access_token'])
            user_info = spotify.current_user()
            session_id = str(uuid.uuid4())

            await self.create_session(
                session_id=session_id,
                device_id=device_info['device_id'],
                platform=device_info['platform'],
                spotify_user_id=user_info['id'],
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                expires_at=int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp())
            )

            logger.info(f"Created session for user {user_info['id']} on device {device_info['device_id']}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to handle Spotify callback: {e}")
            return None

    async def create_session(self, session_id: str, device_id: str, platform: str, spotify_user_id: str, access_token: str, refresh_token: Optional[str], expires_at: int):
        """Create a new auth session"""

        try:
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
                'last_used_at': now
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

            if datetime.now().timestamp() > expires_at:
                await db_service.invalidate_session(session_id)
                return None

            if stored_device_id != device_id:
                device_session = await db_service.get_session_by_device(device_id)

                if not device_session:
                    return None

                device_session_info = await db_service.get_session_info(device_session)

                if not device_session_info or device_session_info['spotify_user_id'] != spotify_user_id:
                    return None

            await db_service.update_session_last_used(session_id)

            return {
                "spotify_user_id": spotify_user_id,
                "device_id": device_id
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

auth_service = AuthService()
