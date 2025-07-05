"""
Database service
Centralizedly manages all database operations.
"""

import aiosqlite
import logging

from typing import Optional, Dict, List, Any
from datetime import datetime

from core.singleton import SingletonServiceBase
from core.models import UserContext

from config.app_constants import AppConstants

logger = logging.getLogger(__name__)

class DatabaseService(SingletonServiceBase):
    """Centralized database service for all database operations"""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize database service."""

        self.db_path = AppConstants.DATABASE_FILENAME
        self._log_initialization("Database service initialized as singleton", logger)

    async def initialize(self):
        """Initialize all database tables (only once)"""

        await self._create_auth_tables()
        await self._create_personality_tables()
        await self._create_playlist_tables()
        await self._create_rate_limit_tables()
        await self._run_migrations()

    async def _create_auth_tables(self):
        """Create authentication-related tables"""

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
                        account_type TEXT DEFAULT 'normal',
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
                logger.info("Auth tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create auth tables: {e}")
            raise

    async def _create_personality_tables(self):
        """Create personality-related tables"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_personalities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        spotify_user_id TEXT,
                        user_context TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id)
                    )
                """)

                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_user_personalities_timestamp 
                    AFTER UPDATE ON user_personalities
                    BEGIN
                        UPDATE user_personalities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                """)

                await db.commit()
                logger.info("Personality tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create personality tables: {e}")
            raise

    async def _create_playlist_tables(self):
        """Create playlist-related tables"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS playlist_drafts (
                        id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        session_id TEXT,
                        prompt TEXT NOT NULL,
                        songs_json TEXT NOT NULL,
                        songs TEXT,
                        refinements_used INTEGER DEFAULT 0,
                        is_draft BOOLEAN DEFAULT 1,
                        status TEXT DEFAULT 'draft',
                        spotify_playlist_id TEXT,
                        spotify_playlist_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_playlist_drafts_timestamp 
                    AFTER UPDATE ON playlist_drafts
                    BEGIN
                        UPDATE playlist_drafts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS echotuner_spotify_playlists (
                        spotify_playlist_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        session_id TEXT,
                        original_draft_id TEXT,
                        playlist_name TEXT NOT NULL,
                        refinements_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_echotuner_spotify_playlists_user_id 
                    ON echotuner_spotify_playlists(user_id)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_echotuner_spotify_playlists_device_id 
                    ON echotuner_spotify_playlists(device_id)
                """)

                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_echotuner_spotify_playlists_timestamp 
                    AFTER UPDATE ON echotuner_spotify_playlists
                    BEGIN
                        UPDATE echotuner_spotify_playlists SET updated_at = CURRENT_TIMESTAMP WHERE spotify_playlist_id = NEW.spotify_playlist_id;
                    END
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS demo_playlists (
                        playlist_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        session_id TEXT,
                        prompt TEXT NOT NULL,
                        refinements_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_demo_playlists_device_id 
                    ON demo_playlists(device_id)
                """)

                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_demo_playlists_timestamp 
                    AFTER UPDATE ON demo_playlists
                    BEGIN
                        UPDATE demo_playlists SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = NEW.playlist_id;
                    END
                """)

                await db.commit()
                logger.info("Playlist tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create playlist tables: {e}")
            raise

    async def _create_rate_limit_tables(self):
        """Create rate limiting tables"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        user_id TEXT PRIMARY KEY,
                        requests_count INTEGER DEFAULT 0,
                        refinements_count INTEGER DEFAULT 0,
                        last_request_date TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_rate_limits_timestamp 
                    AFTER UPDATE ON rate_limits
                    BEGIN
                        UPDATE rate_limits SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
                    END
                """)

                await db.commit()
                logger.info("Rate limit tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create rate limit tables: {e}")
            raise

    async def store_auth_state(self, state: str, device_id: str, platform: str, expires_at: int) -> bool:
        """Store auth state for validation"""

        try:
            data = {
                'state': state,
                'device_id': device_id,
                'platform': platform,
                'created_at': int(datetime.now().timestamp()),
                'expires_at': expires_at
            }

            return await self.insert_or_update('auth_states', data, 'state')

        except Exception as e:
            logger.error(f"Failed to store auth state: {e}")
            return False

    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return device info"""

        try:
            current_time = int(datetime.now().timestamp())
            row = await self.fetch_one("SELECT device_id, platform FROM auth_states WHERE state = ? AND expires_at > ?", (state, current_time))

            if row:
                await self.delete_record('auth_states', 'state = ?', (state,))
                return {"device_id": row[0], "platform": row[1]}

            return None

        except Exception as e:
            logger.error(f"Failed to validate auth state: {e}")
            return None

    async def create_session(self, session_data: Dict[str, Any]) -> bool:
        """Create a new auth session"""

        try:
            return await self.insert_or_update('auth_sessions', session_data, 'session_id')

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False

    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate if session exists and belongs to device"""

        try:
            row = await self.fetch_one("SELECT device_id, expires_at FROM auth_sessions WHERE session_id = ?", (session_id,))
            
            if not row:
                return False

            stored_device_id, expires_at = row

            if stored_device_id != device_id:
                return False

            if datetime.now().timestamp() > expires_at:
                await self.delete_record('auth_sessions', 'session_id = ?', (session_id,))
                return False

            return True

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    async def get_session_by_device(self, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device"""

        try:
            current_time = datetime.now().timestamp()

            row = await self.fetch_one(
                """SELECT session_id FROM auth_sessions 
                   WHERE device_id = ? AND expires_at > ? 
                   ORDER BY created_at DESC LIMIT 1""",
                (device_id, current_time)
            )

            return row[0] if row else None

        except Exception as e:
            logger.error(f"Get session by device error: {e}")
            return None

    async def get_sessions_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a device"""

        try:
            rows = await self.fetch_all(
                """SELECT session_id, device_id, platform, spotify_user_id, 
                          access_token, refresh_token, expires_at, created_at, 
                          last_used_at, account_type 
                   FROM auth_sessions 
                   WHERE device_id = ?""",
                (device_id,)
            )

            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'device_id': row[1],
                    'platform': row[2],
                    'spotify_user_id': row[3],
                    'access_token': row[4],
                    'refresh_token': row[5],
                    'expires_at': row[6],
                    'created_at': row[7],
                    'last_used_at': row[8],
                    'account_type': row[9] if row[9] is not None else 'normal'
                })

            return sessions

        except Exception as e:
            logger.error(f"Get sessions by device error: {e}")
            return []

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""

        try:
            return await self.delete_record('auth_sessions', 'session_id = ?', (session_id,))

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False

    async def register_device(self, device_data: Dict[str, Any]) -> bool:
        """Register a new device"""

        try:
            return await self.insert_or_update('device_registry', device_data, 'device_id')

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False

    async def validate_device(self, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate that device_id was issued by server and is active"""

        try:
            row = await self.fetch_one("SELECT is_active FROM device_registry WHERE device_id = ?", (device_id,))

            if not row or not row[0]:
                return False

            if update_last_seen:
                await self.insert_or_update(
                    'device_registry',
                    {'device_id': device_id, 'last_seen_timestamp': int(datetime.now().timestamp())},
                    'device_id'
                )

            return True

        except Exception as e:
            logger.error(f"Device validation failed: {e}")
            return False

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information including user and device data"""

        try:
            row = await self.fetch_one("""SELECT device_id, expires_at, spotify_user_id, access_token, refresh_token, account_type FROM auth_sessions WHERE session_id = ?""", (session_id,))

            if not row:
                return None

            return {
                'device_id': row[0],
                'expires_at': row[1],
                'spotify_user_id': row[2],
                'access_token': row[3],
                'refresh_token': row[4],
                'account_type': row[5] if row[5] is not None else 'normal'
            }

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None

    async def update_session_token(self, session_id: str, access_token: str, expires_at: int) -> bool:
        """Update session with new access token"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE auth_sessions SET access_token = ?, expires_at = ? WHERE session_id = ?", (access_token, expires_at, session_id))
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to update session token: {e}")
            return False

    async def update_session_last_used(self, session_id: str) -> bool:
        """Update session last used timestamp"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE auth_sessions SET last_used_at = ? WHERE session_id = ?", (int(datetime.now().timestamp()), session_id))
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to update session last used: {e}")
            return False

    async def update_session_expiration(self, session_id: str, expires_at: int) -> bool:
        """Update session expiration time"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE auth_sessions SET expires_at = ? WHERE session_id = ?", (expires_at, session_id))
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to update session expiration: {e}")
            return False

    async def revoke_user_sessions(self, spotify_user_id: str) -> bool:
        """Revoke all sessions for a specific user"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM auth_sessions WHERE spotify_user_id = ?", (spotify_user_id,))
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to revoke user sessions: {e}")
            return False

    async def get_user_active_sessions_count(self, spotify_user_id: str) -> int:
        """Get count of active sessions for a user"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = int(datetime.now().timestamp())
                cursor = await db.execute("SELECT COUNT(*) FROM auth_sessions WHERE spotify_user_id = ? AND expires_at > ?", (spotify_user_id, current_time))
                row = await cursor.fetchone()

                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to get active sessions count: {e}")
            return 0

    async def cleanup_expired_auth_attempts(self) -> bool:
        """Clean up expired authentication attempts"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = int(datetime.now().timestamp())

                await db.execute("DELETE FROM auth_attempts WHERE expires_at < ?", (current_time,))
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to cleanup expired auth attempts: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and states"""

        try:
            current_time = int(datetime.now().timestamp())
            sessions_deleted = await self.cleanup_expired_records('auth_sessions', 'expires_at', current_time)
            states_deleted = await self.cleanup_expired_records('auth_states', 'expires_at', current_time)

            return sessions_deleted + states_deleted

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def get_rate_limit_status(self, user_id: str, current_date: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status for a user"""

        try:
            # Get the most recent record for this user, regardless of date
            row = await self.fetch_one("SELECT requests_count, refinements_count, last_request_date FROM rate_limits WHERE user_id = ? ORDER BY last_request_date DESC LIMIT 1", (user_id,))

            if row:
                return {
                    'requests_count': row[0],
                    'refinements_count': row[1],
                    'last_request_date': row[2]
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return None

    async def update_rate_limit_requests(self, user_id: str, current_date: str, requests_count: int) -> bool:
        """Update rate limit requests count"""

        try:
            # Get existing data to preserve refinements count
            existing = await self.get_rate_limit_status(user_id, current_date)
            refinements_count = existing['refinements_count'] if existing else 0

            data = {
                'user_id': user_id,
                'requests_count': requests_count,
                'refinements_count': refinements_count,
                'last_request_date': current_date
            }

            return await self.insert_or_update('rate_limits', data, 'user_id')

        except Exception as e:
            logger.error(f"Failed to update rate limit requests: {e}")
            return False

    async def update_rate_limit_refinements(self, user_id: str, current_date: str, refinements_count: int) -> bool:
        """Update rate limit refinements count"""

        try:
            existing = await self.get_rate_limit_status(user_id, current_date)

            if existing:
                data = {
                    'user_id': user_id,
                    'requests_count': existing['requests_count'],
                    'refinements_count': refinements_count,
                    'last_request_date': current_date
                }

            else:
                data = {
                    'user_id': user_id,
                    'requests_count': 0,
                    'refinements_count': refinements_count,
                    'last_request_date': current_date
                }

            return await self.insert_or_update('rate_limits', data, 'user_id')

        except Exception as e:
            logger.error(f"Failed to update rate limit refinements: {e}")
            return False

    async def save_playlist_draft(self, draft_data: Dict[str, Any]) -> bool:
        """Save or update playlist draft"""

        try:
            return await self.insert_or_update('playlist_drafts', draft_data, 'id')

        except Exception as e:
            logger.error(f"Failed to save playlist draft: {e}")
            return False

    async def get_playlist_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist draft by ID"""

        try:
            row = await self.fetch_one(
                """SELECT id, device_id, session_id, prompt, songs_json, refinements_used,
                    is_draft, created_at, updated_at, songs, status, spotify_playlist_id, spotify_playlist_url
                    FROM playlist_drafts WHERE id = ?""",
                (draft_id,)
            )

            if row:
                return {
                    'id': row[0],
                    'device_id': row[1],
                    'session_id': row[2],
                    'prompt': row[3],
                    'songs_json': row[4],
                    'refinements_used': row[5],
                    'is_draft': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'songs': row[9],
                    'status': row[10],
                    'spotify_playlist_id': row[11],
                    'spotify_playlist_url': row[12]
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get playlist draft: {e}")
            return None

    async def get_user_drafts(self, device_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's playlist drafts"""

        try:
            rows = await self.fetch_all("SELECT * FROM playlist_drafts WHERE device_id = ? ORDER BY updated_at DESC LIMIT ?", (device_id, limit))
            drafts = []

            for row in rows:
                drafts.append({
                    'id': row[0],
                    'device_id': row[1],
                    'session_id': row[2],
                    'prompt': row[3],
                    'songs_json': row[4],
                    'refinements_used': row[5],
                    'is_draft': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                })

            return drafts

        except Exception as e:
            logger.error(f"Failed to get user drafts: {e}")
            return []

    async def delete_playlist_draft(self, draft_id: str) -> bool:
        """Delete playlist draft"""

        try:
            return await self.delete_record('playlist_drafts', 'id = ?', (draft_id,))

        except Exception as e:
            logger.error(f"Failed to delete playlist draft: {e}")
            return False

    async def update_draft_refinements(self, draft_id: str, refinements_used: int) -> bool:
        """Update refinements used count for a draft"""

        try:
            data = {
                'id': draft_id,
                'refinements_used': refinements_used
            }

            return await self.insert_or_update('playlist_drafts', data, 'id')

        except Exception as e:
            logger.error(f"Failed to update draft refinements: {e}")
            return False

    async def save_user_personality(self, user_id: str, spotify_user_id: str, user_context: UserContext) -> bool:
        """Save or update user personality data"""

        try:
            data = {
                'user_id': user_id,
                'spotify_user_id': spotify_user_id,
                'user_context': user_context.model_dump_json()
            }

            return await self.insert_or_update('user_personalities', data, 'user_id')

        except Exception as e:
            logger.error(f"Failed to save user personality: {e}")
            return False

    async def get_user_personality(self, user_id: str) -> Optional[str]:
        """Get user personality context as JSON string"""

        try:
            row = await self.fetch_one("SELECT user_context FROM user_personalities WHERE user_id = ?", (user_id,))
            return row[0] if row else None

        except Exception as e:
            logger.error(f"Failed to get user personality: {e}")
            return None

    async def execute_query(self, query: str, params: tuple = None) -> Optional[Any]:
        """Execute a single query and return result"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params or ()) as cursor:
                    result = await cursor.fetchone()

                    await db.commit()
                    return result

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    async def execute_many(self, query: str, params_list: List[tuple]):
        """Execute multiple queries with different parameters"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executemany(query, params_list)
                await db.commit()

        except Exception as e:
            logger.error(f"Database batch operation failed: {e}")
            raise

    async def fetch_all(self, query: str, params: tuple = None) -> List[Any]:
        """Fetch all results from a query"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params or ()) as cursor:
                    return await cursor.fetchall()

        except Exception as e:
            logger.error(f"Database fetch failed: {e}")
            raise

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Any]:
        """Fetch one result from a query"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params or ()) as cursor:
                    return await cursor.fetchone()

        except Exception as e:
            logger.error(f"Database fetch failed: {e}")
            raise

    async def insert_or_update(self, table: str, data: Dict[str, Any], conflict_column: str = None) -> bool:
        """Generic insert or update operation"""

        try:
            filtered_data = {k: v for k, v in data.items() if v is not None}
            columns = list(filtered_data.keys())
            values = list(filtered_data.values())

            async with aiosqlite.connect(self.db_path) as db:
                if conflict_column and conflict_column in filtered_data:
                    conflict_value = filtered_data[conflict_column]

                    cursor = await db.execute(
                        f"SELECT 1 FROM {table} WHERE {conflict_column} = ?",
                        (conflict_value,)
                    )

                    exists = await cursor.fetchone()
                    await cursor.close()

                    if exists:
                        set_clauses = [f"{col} = ?" for col in columns if col != conflict_column]
                        update_values = [v for k, v in filtered_data.items() if k != conflict_column]
                        update_values.append(conflict_value)

                        query = f"""
                            UPDATE {table} 
                            SET {', '.join(set_clauses)}
                            WHERE {conflict_column} = ?
                        """

                        await db.execute(query, update_values)

                    else:
                        placeholders = ', '.join(['?' for _ in columns])

                        query = f"""
                            INSERT INTO {table} 
                            ({', '.join(columns)}) 
                            VALUES ({placeholders})
                        """

                        await db.execute(query, values)

                else:
                    placeholders = ', '.join(['?' for _ in columns])

                    query = f"""
                        INSERT INTO {table} 
                        ({', '.join(columns)}) 
                        VALUES ({placeholders})
                    """

                    await db.execute(query, values)

                await db.commit()
                return True

        except Exception as e:
            logger.error(f"Database insert/update failed: {e}")
            return False

    async def delete_record(self, table: str, where_clause: str, params: tuple = None) -> bool:
        """Generic delete operation"""

        try:
            query = f"DELETE FROM {table} WHERE {where_clause}"

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params or ())
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Database delete failed: {e}")
            return False

    async def cleanup_expired_records(self, table: str, timestamp_column: str, expiry_timestamp: int) -> int:
        """Clean up expired records from any table"""

        try:
            query = f"DELETE FROM {table} WHERE {timestamp_column} < ?"

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, (expiry_timestamp,))
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} expired records from {table}")

                await db.commit()
                return deleted_count

        except Exception as e:
            logger.error(f"Cleanup failed for {table}: {e}")
            return 0

    async def _run_migrations(self):
        """Run database migrations to add missing columns"""

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Migrate playlist_drafts table
                cursor = await db.execute("PRAGMA table_info(playlist_drafts)")
                columns = await cursor.fetchall()
                existing_columns = [col[1] for col in columns]
                migrations = []

                if 'songs' not in existing_columns:
                    migrations.append("ALTER TABLE playlist_drafts ADD COLUMN songs TEXT")

                if 'status' not in existing_columns:
                    migrations.append("ALTER TABLE playlist_drafts ADD COLUMN status TEXT DEFAULT 'draft'")

                if 'spotify_playlist_id' not in existing_columns:
                    migrations.append("ALTER TABLE playlist_drafts ADD COLUMN spotify_playlist_id TEXT")

                if 'spotify_playlist_url' not in existing_columns:
                    migrations.append("ALTER TABLE playlist_drafts ADD COLUMN spotify_playlist_url TEXT")

                # Migrate auth_sessions table
                cursor = await db.execute("PRAGMA table_info(auth_sessions)")
                columns = await cursor.fetchall()
                auth_columns = [col[1] for col in columns]
                
                if 'account_type' not in auth_columns:
                    migrations.append("ALTER TABLE auth_sessions ADD COLUMN account_type TEXT DEFAULT 'normal'")

                for migration in migrations:
                    await db.execute(migration)
                    logger.info(f"Applied migration: {migration}")

                await db.commit()

                if migrations:
                    logger.info(f"Applied {len(migrations)} database migrations")

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            raise

    async def cleanup_demo_sessions(self):
        """Clean up all demo account sessions"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM auth_sessions 
                    WHERE account_type = 'demo'
                """)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup demo sessions: {e}")
            raise

    async def cleanup_normal_sessions(self):
        """Clean up all normal account sessions"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM auth_sessions 
                    WHERE account_type = 'normal' OR account_type IS NULL
                """)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup normal sessions: {e}")
            raise

    async def get_all_sessions_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific device"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT session_id, spotify_user_id, account_type, expires_at 
                    FROM auth_sessions 
                    WHERE device_id = ?
                """, (device_id,))
                
                rows = await cursor.fetchall()
                return [
                    {
                        "session_id": row[0],
                        "spotify_user_id": row[1], 
                        "account_type": row[2] or 'normal',
                        "expires_at": row[3]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get sessions for device: {e}")
            return []

    async def cleanup_device_auth_states(self, device_id: str):
        """Clean up all auth states for a specific device"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM auth_states 
                    WHERE device_id = ?
                """, (device_id,))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup device auth states: {e}")
            raise

    async def cleanup_user_rate_limits(self, user_id: str):
        """Clean up all rate limit data for a specific user ID (for demo accounts)"""
        
        try:
            # Get the user hash (same as rate limiter service uses)
            import hashlib
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM rate_limits 
                    WHERE user_id = ?
                """, (user_hash,))
                await db.commit()
                logger.info(f"Cleaned up rate limits for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup user rate limits: {e}")

    async def cleanup_device_rate_limits(self, device_id: str):
        """Clean up all rate limit data for a specific device"""
        
        try:
            # Get the device hash (same as rate limiter service uses)
            import hashlib
            device_hash = hashlib.sha256(device_id.encode()).hexdigest()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM rate_limits 
                    WHERE user_id = ?
                """, (device_hash,))
                await db.commit()
                logger.info(f"Cleaned up rate limits for device {device_id[:8]}...")
                
        except Exception as e:
            logger.error(f"Failed to cleanup device rate limits: {e}")

    # Demo playlist management
    async def add_demo_playlist(self, playlist_id: str, device_id: str, session_id: str, prompt: str):
        """Add a demo playlist ID to track refinement counts"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO demo_playlists 
                    (playlist_id, device_id, session_id, prompt, refinements_used, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (playlist_id, device_id, session_id, prompt))
                await db.commit()
                logger.info(f"Added demo playlist {playlist_id} for device {device_id}")
                
        except Exception as e:
            logger.error(f"Failed to add demo playlist {playlist_id}: {e}")
            raise

    async def get_demo_playlist_refinements(self, playlist_id: str) -> int:
        """Get the refinement count for a demo playlist"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT refinements_used FROM demo_playlists 
                    WHERE playlist_id = ?
                """, (playlist_id,))
                
                row = await cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            logger.error(f"Failed to get demo playlist refinements for {playlist_id}: {e}")
            return 0

    async def increment_demo_playlist_refinements(self, playlist_id: str):
        """Increment the refinement count for a demo playlist"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE demo_playlists 
                    SET refinements_used = refinements_used + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE playlist_id = ?
                """, (playlist_id,))
                await db.commit()
                logger.info(f"Incremented refinement count for demo playlist {playlist_id}")
                
        except Exception as e:
            logger.error(f"Failed to increment refinements for demo playlist {playlist_id}: {e}")
            raise

    async def get_demo_playlists_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all demo playlist IDs for a device"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT playlist_id, prompt, refinements_used, created_at, updated_at
                    FROM demo_playlists 
                    WHERE device_id = ?
                    ORDER BY created_at DESC
                """, (device_id,))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'playlist_id': row[0],
                        'prompt': row[1],
                        'refinements_used': row[2],
                        'created_at': row[3],
                        'updated_at': row[4]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get demo playlists for device {device_id}: {e}")
            return []

    async def cleanup_demo_playlists_for_device(self, device_id: str):
        """Clean up all demo playlists for a specific device"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM demo_playlists 
                    WHERE device_id = ?
                """, (device_id,))
                await db.commit()
                logger.info(f"Cleaned up demo playlists for device {device_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup demo playlists for device {device_id}: {e}")
            raise

db_service = DatabaseService()
