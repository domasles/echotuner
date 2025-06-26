"""Authentication service for Spotify OAuth and session management."""

import aiosqlite
import secrets
import uuid

import logging
import spotipy

from datetime import datetime, timedelta
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict

from config.settings import settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db_path = "echotuner.db"
        self.spotify_oauth = None
        self._initialize_spotify_oauth()

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
                scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative",
                show_dialog=True
            )

            logger.info("Spotify OAuth initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Spotify OAuth: {e}")

    async def initialize(self):
        """Initialize database tables"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS device_registry (
                        device_id TEXT PRIMARY KEY,
                        platform TEXT NOT NULL,
                        app_version TEXT,
                        device_fingerprint TEXT,
                        registration_timestamp INTEGER NOT NULL,
                        last_seen_timestamp INTEGER NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        session_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        spotify_user_id TEXT,
                        access_token TEXT,
                        refresh_token TEXT,
                        expires_at INTEGER,
                        created_at INTEGER NOT NULL,
                        last_used_at INTEGER NOT NULL,
                        UNIQUE(device_id)
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS auth_states (
                        state TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL
                    )
                """)

                await db.commit()
                logger.info("Auth database tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize auth database: {e}")
            raise

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
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO auth_states 
                    (state, device_id, platform, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (state, device_id, platform, int(datetime.now().timestamp()), expires_at))

                await db.commit()

        except Exception as e:
            logger.error(f"Failed to store auth state: {e}")
            raise

    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return device info"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT device_id, platform FROM auth_states 
                    WHERE state = ? AND expires_at > ?
                """, (state, int(datetime.now().timestamp()))) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        await db.execute("DELETE FROM auth_states WHERE state = ?", (state,))
                        await db.commit()
                        
                        return {"device_id": row[0], "platform": row[1]}
                    
            return None
        
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
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO auth_sessions 
                    (session_id, device_id, platform, spotify_user_id, access_token, 
                     refresh_token, expires_at, created_at, last_used_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, device_id, platform, spotify_user_id, access_token, refresh_token, expires_at, now, now))
                
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate if session exists and belongs to device"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT device_id, expires_at FROM auth_sessions WHERE session_id = ?", (session_id)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        return False
                    
                    stored_device_id, expires_at = row

                    if stored_device_id != device_id:
                        return False
                    
                    if datetime.now().timestamp() > expires_at:
                        await db.execute("DELETE FROM auth_sessions WHERE session_id = ?", (session_id,))
                        await db.commit()
                        
                        return False
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    async def get_session_by_device(self, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device (for desktop polling)"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """SELECT session_id, expires_at FROM auth_sessions 
                       WHERE device_id = ? AND expires_at > ? 
                       ORDER BY created_at DESC LIMIT 1
                    """, (device_id, datetime.now().timestamp())) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        return row[0]
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Get session by device error: {e}")
            return None

    async def invalidate_session(self, session_id: str):
        """Invalidate a session"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM auth_sessions WHERE session_id = ?", (session_id,))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions and states"""
        
        try:
            now = int(datetime.now().timestamp())
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (now,))
                await db.execute("DELETE FROM auth_states WHERE expires_at < ?", (now,))
                await db.commit()

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
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO device_registry 
                    (device_id, platform, app_version, device_fingerprint, registration_timestamp, last_seen_timestamp, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (device_id, platform, app_version, device_fingerprint, registration_timestamp, registration_timestamp))
                
                await db.commit()
                
                logger.info(f"Registered new device: {device_id} on {platform}")
                return device_id, registration_timestamp
                
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            raise Exception("Device registration failed")

    async def validate_device(self, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate that device_id was issued by server and is active"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT is_active, platform FROM device_registry WHERE device_id = ?", (device_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        logger.warning(f"Unknown device ID: {device_id}")
                        return False
                    
                    is_active, platform = row
                    
                    if not is_active:
                        logger.warning(f"Inactive device ID: {device_id}")
                        return False

                    if update_last_seen:
                        await db.execute("UPDATE device_registry SET last_seen_timestamp = ? WHERE device_id = ?", (int(datetime.now().timestamp()), device_id))
                        await db.commit()
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Device validation failed: {e}")
            return False

    async def validate_session_and_get_user(self, session_id: str, device_id: str) -> Optional[Dict[str, str]]:
        """Validate session and return user info if valid"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT device_id, expires_at, spotify_user_id FROM auth_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    stored_device_id, expires_at, spotify_user_id = row

                    if stored_device_id != device_id:
                        return None
                    
                    if datetime.now().timestamp() > expires_at:
                        await db.execute("DELETE FROM auth_sessions WHERE session_id = ?", (session_id,))
                        await db.commit()

                        return None

                    await db.execute("UPDATE auth_sessions SET last_used_at = ? WHERE session_id = ?", (int(datetime.now().timestamp()), session_id))
                    await db.commit()
                    
                    return {
                        "spotify_user_id": spotify_user_id,
                        "device_id": stored_device_id
                    }
                    
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
