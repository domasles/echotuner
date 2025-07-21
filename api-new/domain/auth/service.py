"""
Clean Auth service - manages its own data operations via repository.
No dependency on monolithic database service.
"""

import asyncio
import logging
import secrets
import spotipy
import uuid
from spotipy.cache_handler import CacheFileHandler
from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict, Any, List

from application.core.singleton import SingletonServiceBase
from infrastructure.config.settings import settings
from infrastructure.database import repository
from infrastructure.database.models import AuthSession, DeviceRegistry, AuthState, AuthAttempt, DemoOwnerToken
from infrastructure.config.app_constants import app_constants

logger = logging.getLogger(__name__)

class AuthService(SingletonServiceBase):
    """Clean auth service managing its own data via repository."""

    def __init__(self):
        super().__init__()
        self._demo_owner_token_info = None
        self._demo_owner_lock = asyncio.Lock()

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
        try:
            # Clean up any demo data on startup
            await self._cleanup_demo_data()
            
            # Load demo owner token if in demo mode
            if settings.DEMO:
                await self._load_demo_owner_token()
            
            logger.info("Auth service async initialization completed")
        except Exception as e:
            logger.error(f"Auth service async initialization failed: {e}")

    # AUTH STATE MANAGEMENT
    async def generate_auth_url(self, device_id: str, platform: str) -> tuple[str, str]:
        """Generate Spotify authorization URL and state."""
        if not self.spotify_oauth:
            raise Exception("Spotify OAuth not configured")

        state = secrets.token_urlsafe(32)
        auth_url = self.spotify_oauth.get_authorize_url(state=state)
        
        # Store state for validation
        await self.store_auth_state(state, device_id, platform)
        
        return auth_url, state

    async def store_auth_state(self, state: str, device_id: str, platform: str) -> bool:
        """Store auth state for validation."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            # Check if state already exists and delete it first
            existing_state = await self.repo.get_by_field(AuthState, 'state', state)
            if existing_state:
                await self.repo.delete(AuthState, existing_state.state, 'state')
            
            auth_state_data = {
                'state': state,
                'device_id': device_id,
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
        """Validate auth state and return device info."""
        try:
            auth_state = await self.repo.get_by_field(AuthState, 'state', state)
            
            if not auth_state:
                return None
                
            # Check if expired
            if auth_state.expires_at < int(datetime.utcnow().timestamp()):
                await self.repo.delete(AuthState, auth_state.state, 'state')
                return None

            return {
                'device_id': auth_state.device_id,
                'platform': auth_state.platform
            }
            
        except Exception as e:
            logger.error(f"Failed to validate auth state: {e}")
            return None

    # SESSION MANAGEMENT
    async def create_session(self, session_data: Dict[str, Any]) -> bool:
        """Create new auth session."""
        try:
            logger.info(f"Creating session for device: {session_data.get('device_id')} with session_id: {session_data.get('session_id')}")
            
            # Business logic: check for existing sessions for this device
            existing_sessions = await self.repo.list_by_field(
                AuthSession, 'device_id', session_data['device_id']
            )
            
            logger.info(f"Found {len(existing_sessions)} existing sessions for device")
            
            # Clean up old sessions for this device
            for session in existing_sessions:
                logger.info(f"Deleting existing session: {session.session_id}")
                await self.repo.delete(AuthSession, session.session_id, 'session_id')
            
            # Add timestamps as integers
            session_data['created_at'] = int(datetime.utcnow().timestamp())
            session_data['last_used_at'] = int(datetime.utcnow().timestamp())
            session_data['expires_at'] = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            
            logger.info(f"Creating new session with data: {session_data}")
            await self.repo.create(AuthSession, session_data)
            
            logger.info("Session created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False

    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate session belongs to device."""
        try:
            session = await self.repo.get_by_conditions(AuthSession, {
                'session_id': session_id,
                'device_id': device_id
            })
            
            if not session:
                return False
                
            # Check if expired (compare timestamps)
            if session.expires_at < int(datetime.utcnow().timestamp()):
                await self.repo.delete(AuthSession, session.session_id, 'session_id')
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False

    async def validate_session_and_get_user(self, session_id: str, device_id: str) -> Optional[Dict[str, str]]:
        """Validate session and return user info if valid."""
        try:
            session = await self.repo.get_by_field(AuthSession, 'session_id', session_id)

            if not session:
                return None

            stored_device_id = session.device_id
            expires_at = session.expires_at
            spotify_user_id = session.spotify_user_id
            account_type = getattr(session, 'account_type', 'normal')

            # Demo mode validation
            if settings.DEMO and account_type == 'normal':
                return None

            if not settings.DEMO and account_type == 'demo':
                return None

            if stored_device_id != device_id:
                return None

            # Check if expired (compare timestamps)
            if int(datetime.now().timestamp()) > expires_at:
                await self.repo.delete(AuthSession, session.session_id, 'session_id')
                return None

            # Update last_used_at timestamp
            await self.repo.update(AuthSession, session.session_id, {
                'last_used_at': int(datetime.now().timestamp())
            }, 'session_id')

            return {
                "spotify_user_id": spotify_user_id,
                "device_id": device_id,
                "account_type": account_type
            }

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def get_account_type(self, session_id: str) -> Optional[str]:
        """Get account type for a session."""
        try:
            session = await self.repo.get_by_field(AuthSession, 'session_id', session_id)

            if not session:
                return None

            return getattr(session, 'account_type', 'normal')

        except Exception as e:
            logger.error(f"Failed to get account type: {e}")
            return None

    async def get_session_by_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get active session for device."""
        try:
            sessions = await self.repo.list_by_field(AuthSession, 'device_id', device_id)
            
            for session in sessions:
                # Check if expired (convert datetime to timestamp for comparison)
                if session.expires_at < int(datetime.utcnow().timestamp()):
                    await self.repo.delete(AuthSession, session.session_id, 'session_id')
                    continue
                    
                return {
                    'session_id': session.session_id,
                    'account_type': session.account_type,
                    'created_at': session.created_at,
                    'expires_at': session.expires_at
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session by device: {e}")
            return None

    async def invalidate_session(self, session_id: str):
        """Invalidate a session."""
        try:
            session = await self.repo.get_by_field(AuthSession, 'session_id', session_id)
            if session:
                await self.repo.delete(AuthSession, session.session_id, 'session_id')
                
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            # Get all sessions
            all_sessions = await self.repo.list_all(AuthSession)
            expired_count = 0
            
            for session in all_sessions:
                if session.expires_at < int(datetime.utcnow().timestamp()):
                    await self.repo.delete(AuthSession, session.session_id, 'session_id')
                    expired_count += 1
                    
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
                
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    # DEVICE MANAGEMENT
    async def register_device(self, device_data: Dict[str, Any]) -> bool:
        """Register a new device."""
        try:
            # Check if device already exists
            existing = await self.repo.get_by_field(
                DeviceRegistry, 'device_id', device_data['device_id']
            )
            
            if existing:
                # Update existing device info
                update_data = {
                    'last_seen_timestamp': int(datetime.utcnow().timestamp()),
                    'app_version': device_data.get('app_version', existing.app_version)
                }
                await self.repo.update(DeviceRegistry, existing.device_id, update_data, 'device_id')
                return True
            
            # Create new device registration with correct timestamps
            if 'registration_timestamp' not in device_data:
                device_data['registration_timestamp'] = int(datetime.utcnow().timestamp())
            if 'last_seen_timestamp' not in device_data:
                device_data['last_seen_timestamp'] = int(datetime.utcnow().timestamp())
            
            await self.repo.create(DeviceRegistry, device_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False

    async def validate_device(self, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate device is registered."""
        try:
            device = await self.repo.get_by_field(DeviceRegistry, 'device_id', device_id)
            
            if not device:
                return False
                
            if update_last_seen:
                await self.repo.update(DeviceRegistry, device.device_id, {
                    'last_seen': datetime.utcnow()
                }, id_field='device_id')
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate device: {e}")
            return False

    # DEMO MODE MANAGEMENT
    async def _cleanup_demo_data(self):
        """Clean up demo data on startup."""
        try:
            # Get demo sessions
            demo_sessions = await self.repo.list_by_field(AuthSession, 'account_type', 'demo')
            
            # Clean up demo sessions
            for session in demo_sessions:
                await self.repo.delete(AuthSession, session.session_id, 'session_id')
                
            # NOTE: DO NOT delete demo owner token - it needs to persist across restarts!
            # Only clean up expired sessions and temporary data
                
            logger.info("Demo data cleanup completed (preserved owner token)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup demo data: {e}")

    async def store_demo_owner_token(self, token_info: Dict[str, Any]):
        """Store demo owner token."""
        try:
            # Clear existing demo tokens
            existing_tokens = await self.repo.list_all(DemoOwnerToken)
            for token in existing_tokens:
                await self.repo.delete(DemoOwnerToken, token.id)
                
            # Store new token
            token_data = {
                'access_token': token_info.get('access_token'),
                'refresh_token': token_info.get('refresh_token'),
                'expires_at': datetime.fromtimestamp(token_info.get('expires_at', 0)),
                'created_at': datetime.utcnow()
            }
            
            await self.repo.create(DemoOwnerToken, token_data)
            
        except Exception as e:
            logger.error(f"Failed to store demo owner token: {e}")

    async def get_demo_owner_token(self) -> Optional[Dict[str, Any]]:
        """Get demo owner token."""
        try:
            tokens = await self.repo.list_all(DemoOwnerToken)
            if not tokens:
                return None
                
            token = tokens[0]  # Get first token
            
            return {
                'access_token': token.access_token,
                'refresh_token': token.refresh_token,
                'expires_at': int(token.expires_at.timestamp())
            }
            
        except Exception as e:
            logger.error(f"Failed to get demo owner token: {e}")
            return None

    def get_info(self):
        """Get service information."""
        return {
            'service_type': 'domain',
            'service_name': 'auth_service',
            'description': 'Clean authentication service with repository pattern',
            'dependencies': ['repository'],
            'status': 'initialized'
        }

    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return True  # Auth service is always ready since it uses repository pattern

    def has_demo_owner_token(self) -> bool:
        """Check if demo mode has an owner token stored."""
        from infrastructure.config.settings import settings
        return settings.DEMO and self._demo_owner_token_info is not None

    async def handle_spotify_callback(self, code: str, state: str, device_info: Dict) -> Optional[str]:
        """Handle Spotify OAuth callback."""
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

            session_data = {
                'session_id': session_id,
                'device_id': device_id,
                'platform': device_info['platform'],
                'spotify_user_id': demo_user_id,
                'access_token': token_info['access_token'],
                'refresh_token': token_info.get('refresh_token'),
                'expires_at': int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp()),
                'account_type': account_type
            }

            await self.create_session(session_data)

            return session_id

        except Exception as e:
            logger.error(f"Failed to handle Spotify callback: {e}")
            return None

    async def _store_demo_owner_token(self):
        """Store demo owner token to database."""
        try:
            logger.info(f"_store_demo_owner_token called, has token info: {self._demo_owner_token_info is not None}")
            if not self._demo_owner_token_info:
                logger.warning("No demo owner token info to store")
                return

            logger.info(f"Storing demo owner token for user: {self._demo_owner_token_info['spotify_user_id']}")

            # Clear existing demo owner tokens
            existing_tokens = await self.repo.list_all(DemoOwnerToken)
            logger.info(f"Found {len(existing_tokens)} existing demo owner tokens to clear")
            for token in existing_tokens:
                await self.repo.delete(DemoOwnerToken, token.id)

            # Store new token
            token_data = {
                'access_token': self._demo_owner_token_info['access_token'],
                'refresh_token': self._demo_owner_token_info.get('refresh_token'),
                'expires_at': self._demo_owner_token_info['expires_at'],
                'spotify_user_id': self._demo_owner_token_info['spotify_user_id'],
                'created_at': int(datetime.now().timestamp())
            }

            logger.info(f"Creating demo owner token record: {token_data}")
            result = await self.repo.create(DemoOwnerToken, token_data)
            logger.info(f"Demo owner token stored successfully, result: {result}")

        except Exception as e:
            logger.error(f"Failed to store demo owner token: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")

    async def _load_demo_owner_token(self):
        """Load demo owner token from database on startup."""
        try:
            logger.info("Loading demo owner token from database...")
            tokens = await self.repo.list_all(DemoOwnerToken)
            if tokens:
                token = tokens[0]  # Should only be one token
                self._demo_owner_token_info = {
                    'access_token': token.access_token,
                    'refresh_token': token.refresh_token,
                    'expires_at': token.expires_at,
                    'spotify_user_id': token.spotify_user_id
                }
                current_time = int(datetime.now().timestamp())
                is_expired = current_time > token.expires_at
                logger.info(f"Loaded demo owner token for user: {token.spotify_user_id}")
                logger.info(f"Token expires at: {token.expires_at}, current time: {current_time}, expired: {is_expired}")
                
                # If token is expired but we have refresh token, refresh it immediately
                if is_expired and token.refresh_token:
                    logger.info("Demo owner token is expired, attempting refresh...")
                    try:
                        token_info = self.spotify_oauth.refresh_access_token(token.refresh_token)
                        self._demo_owner_token_info.update({
                            'access_token': token_info['access_token'],
                            'expires_at': int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp())
                        })
                        await self._store_demo_owner_token()
                        logger.info("Successfully refreshed demo owner token on startup")
                    except Exception as e:
                        logger.error(f"Failed to refresh demo owner token on startup: {e}")
                        # Keep the expired token, it will be refreshed on first use
                
            else:
                self._demo_owner_token_info = None
                logger.info("No demo owner token found in database")
        except Exception as e:
            logger.error(f"Failed to load demo owner token: {e}")
            self._demo_owner_token_info = None

    async def invalidate_device_completely(self, device_id: str):
        """Completely invalidate all sessions and data for a device"""
        try:
            # Get all sessions for the device
            sessions = await self.repo.list_with_conditions(AuthSession, {
                'device_id': device_id
            })
            
            demo_sessions = [s for s in sessions if s.account_type == 'demo']

            # Invalidate all sessions
            for session in sessions:
                await self.repo.update(AuthSession, session.session_id, {
                    'is_active': False,
                    'updated_at': int(datetime.now().timestamp())
                }, id_field='session_id')
                logger.debug(f"Invalidated session {session.session_id[:8]}... for device {device_id[:8]}...")

            # Delete demo account data if any demo sessions existed
            if demo_sessions:
                await self._delete_demo_account_data(device_id, demo_sessions)

            # Clean up auth states for the device
            auth_states = await self.repo.list_with_conditions(AuthState, {
                'device_id': device_id
            })
            for state in auth_states:
                await self.repo.delete(AuthState, state.state, id_field='state')

            logger.debug(f"Completely invalidated device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to completely invalidate device: {e}")

    async def _delete_demo_account_data(self, device_id: str, demo_sessions: list):
        """Delete all demo account data for a specific device"""
        try:
            demo_user_id = f"demo_user_{device_id}"
            
            # Delete user personality data
            from infrastructure.database.models.users import UserPersonality
            user_personality = await self.repo.get_by_field(UserPersonality, 'user_id', demo_user_id)
            if user_personality:
                await self.repo.delete(UserPersonality, user_personality.id)

            # Delete playlist drafts associated with demo sessions
            from infrastructure.database.models.playlists import PlaylistDraft, DemoPlaylist
            session_ids = [session.session_id for session in demo_sessions]
            
            for session_id in session_ids:
                # Delete playlist drafts
                drafts = await self.repo.list_with_conditions(PlaylistDraft, {
                    'session_id': session_id
                })
                for draft in drafts:
                    await self.repo.delete(PlaylistDraft, draft.id)

                # Delete demo playlists
                demo_playlists = await self.repo.list_with_conditions(DemoPlaylist, {
                    'session_id': session_id
                })
                for playlist in demo_playlists:
                    await self.repo.delete(DemoPlaylist, playlist.playlist_id, id_field='playlist_id')

            logger.debug(f"Deleted demo account data for device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to delete demo account data: {e}")

    async def get_access_token(self, session_id: str) -> Optional[str]:
        """Get access token for a session."""
        try:
            # In demo mode, always use owner's token regardless of session
            if settings.DEMO:
                async with self._demo_owner_lock:
                    if self._demo_owner_token_info:
                        # Check if owner token is expired and refresh if needed
                        current_time = int(datetime.now().timestamp())
                        if current_time > self._demo_owner_token_info['expires_at']:
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
            session = await self.repo.get_by_field(AuthSession, 'session_id', session_id)

            if not session:
                return None

            current_time = int(datetime.now().timestamp())
            
            # Check if token needs refresh
            if current_time > session.expires_at:
                if session.refresh_token and self.spotify_oauth:
                    try:
                        token_info = self.spotify_oauth.refresh_access_token(session.refresh_token)
                        new_access_token = token_info['access_token']
                        new_expires_at = int((datetime.now() + timedelta(seconds=token_info['expires_in'])).timestamp())

                        await self.repo.update(AuthSession, session.session_id, {
                            'access_token': new_access_token,
                            'expires_at': new_expires_at,
                            'updated_at': current_time
                        }, id_field='session_id')
                        
                        return new_access_token

                    except Exception as e:
                        logger.error(f"Failed to refresh token: {e}")
                        return None
                else:
                    logger.warning(f"Session {session_id} token expired and no refresh token available")
                    return None

            return session.access_token

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None

    async def get_user_from_session(self, session_id: str) -> Optional[Dict]:
        """Get user information from session ID."""
        try:
            session = await self.repo.get_by_field(AuthSession, 'session_id', session_id)

            if not session:
                return None

            return {
                'spotify_user_id': session.spotify_user_id,
                'device_id': session.device_id
            }
        except Exception as e:
            logger.error(f"Failed to get user from session: {e}")
            return None

    async def create_demo_bypass_session(self, device_id: str, platform: str) -> str:
        """Create a demo session that bypasses OAuth (for subsequent users after owner)."""
        session_id = str(uuid.uuid4())
        demo_user_id = f"demo_user_{device_id}"

        # Use a dummy token since we'll use owner's token for actual API calls
        session_data = {
            'session_id': session_id,
            'device_id': device_id,
            'platform': platform,
            'spotify_user_id': demo_user_id,
            'access_token': "demo_bypass_token",
            'refresh_token': None,
            'expires_at': int((datetime.now() + timedelta(days=30)).timestamp()),
            'created_at': int(datetime.now().timestamp()),
            'last_used_at': int(datetime.now().timestamp()),
            'account_type': "demo"
        }

        await self.create_session(session_data)
        return session_id

# Global service instance
auth_service = AuthService()
