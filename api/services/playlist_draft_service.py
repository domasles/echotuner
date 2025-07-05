"""
Playlist draft service.
Manages playlist drafts, including saving, updating, and cleaning up expired drafts.
"""

import asyncio
import logging
import sqlite3
import uuid
import json

from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from core.singleton import SingletonServiceBase
from core.models import PlaylistDraft, Song

from config.app_constants import AppConstants
from config.settings import settings

from services.database_service import db_service

logger = logging.getLogger(__name__)

class PlaylistDraftService(SingletonServiceBase):
    """Service for managing playlist drafts and Spotify playlist integration."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the PlaylistDraftService."""

        self.db_path = Path(__file__).parent.parent / AppConstants.DATABASE_FILENAME
        self._cleanup_task = None

        self._log_initialization("Playlist draft service initialized successfully", logger)

    async def initialize(self):
        """Initialize the playlist draft service."""

        try:
            await self._start_cleanup_task()
            logger.info("Playlist draft service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize playlist draft service: {e}")
            raise

    async def _start_cleanup_task(self):
        """Start the background cleanup task for expired drafts."""

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_drafts_loop())

    async def _cleanup_expired_drafts_loop(self):
        """Background task to clean up expired drafts."""

        while True:
            try:
                await asyncio.sleep(settings.DRAFT_CLEANUP_INTERVAL * 3600)
                await self._cleanup_expired_drafts()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _cleanup_expired_drafts(self):
        """Remove expired draft playlists."""

        try:
            cutoff_timestamp = int((datetime.now() - timedelta(days=settings.DRAFT_STORAGE_TIMEOUT)).timestamp())
            deleted_count = await db_service.cleanup_expired_records('playlist_drafts', 'created_at', cutoff_timestamp)

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired draft playlists")

        except Exception as e:
            logger.error(f"Failed to cleanup expired drafts: {e}")

    async def save_draft(self, device_id: str, session_id: Optional[str], prompt: str, songs: List[Song], refinements_used: int = 0) -> str:
        """Save a playlist as a draft."""

        try:
            playlist_id = str(uuid.uuid4())
            now = datetime.now()
            songs_json = [song.model_dump() for song in songs]

            draft_data = {
                'id': playlist_id,
                'device_id': device_id,
                'session_id': session_id,
                'prompt': prompt,
                'songs_json': json.dumps(songs_json),
                'refinements_used': refinements_used,
                'is_draft': True,
                'status': 'draft',
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }

            success = await db_service.save_playlist_draft(draft_data)
            if success:
                logger.info(f"Saved draft playlist {playlist_id} for device {device_id}")
                return playlist_id
            else:
                raise Exception("Failed to save to database")

        except Exception as e:
            logger.error(f"Failed to save draft playlist: {e}")
            raise

    async def update_draft(self, playlist_id: str, songs: List[Song], refinements_used: int, prompt: Optional[str] = None) -> bool:
        """Update an existing draft playlist."""

        try:
            songs_json = [song.model_dump() for song in songs]
            now = datetime.now()
            existing_draft = await db_service.get_playlist_draft(playlist_id)

            if not existing_draft or not existing_draft.get('is_draft', False):
                logger.warning(f"Failed to update draft playlist {playlist_id} - not found or not draft")
                return False

            draft_data = {
                'id': playlist_id,
                'device_id': existing_draft['device_id'],
                'session_id': existing_draft['session_id'],
                'prompt': prompt if prompt is not None else existing_draft['prompt'],
                'songs_json': json.dumps(songs_json),
                'refinements_used': refinements_used,
                'is_draft': existing_draft['is_draft'],
                'status': 'draft',
                'created_at': existing_draft['created_at'],
                'updated_at': now.isoformat()
            }

            success = await db_service.save_playlist_draft(draft_data)

            if success:
                logger.info(f"Updated draft playlist {playlist_id}")

            else:
                logger.warning(f"Failed to update draft playlist {playlist_id} - database error")

            return success

        except Exception as e:
            logger.error(f"Failed to update draft playlist {playlist_id}: {e}")
            return False

    async def mark_as_added_to_spotify(self, playlist_id: str, spotify_playlist_id: str, spotify_url: str, user_id: str = None, device_id: str = None, session_id: str = None, playlist_name: str = None) -> bool:
        """Mark a draft as added to Spotify and record the Spotify playlist."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE playlist_drafts 
                    SET status = 'added_to_spotify', 
                        spotify_playlist_id = ?, 
                        spotify_playlist_url = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (spotify_playlist_id, spotify_url, datetime.now(), playlist_id))

                success = cursor.rowcount > 0

                if success and user_id and device_id and playlist_name:
                    cursor.execute('''
                        SELECT refinements_used FROM playlist_drafts WHERE id = ?
                    ''', (playlist_id,))

                    draft_row = cursor.fetchone()
                    refinements_used = draft_row[0] if draft_row else 0

                    insert_playlist_sql = f'''
                        INSERT OR REPLACE INTO {AppConstants.SPOTIFY_PLAYLISTS_TABLE} 
                        (spotify_playlist_id, user_id, device_id, session_id, original_draft_id, 
                         playlist_name, refinements_used, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''

                    cursor.execute(insert_playlist_sql, (spotify_playlist_id, user_id, device_id, session_id, playlist_id, playlist_name, refinements_used, datetime.now(), datetime.now()))

                conn.commit()

            if success:
                logger.info(f"Marked playlist {playlist_id} as added to Spotify ({spotify_playlist_id})")

            else:
                logger.warning(f"Failed to mark playlist {playlist_id} as added to Spotify - not found")

            return success

        except Exception as e:
            logger.error(f"Failed to mark playlist {playlist_id} as added to Spotify: {e}")
            raise

    async def get_user_echotuner_spotify_playlist_ids(self, user_id: str) -> List[str]:
        """Get list of Spotify playlist IDs created by EchoTuner for a user."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                select_playlists_sql = f'''
                    SELECT spotify_playlist_id 
                    FROM {AppConstants.SPOTIFY_PLAYLISTS_TABLE} 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                '''

                cursor.execute(select_playlists_sql, (user_id,))
                rows = cursor.fetchall()

            return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get EchoTuner Spotify playlist IDs for user {user_id}: {e}")
            raise

    async def get_draft(self, playlist_id: str) -> Optional[PlaylistDraft]:
        """Get a specific draft playlist."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, device_id, session_id, prompt, songs_json, created_at, 
                    updated_at, refinements_used, status, spotify_playlist_id
                    FROM playlist_drafts 
                    WHERE id = ?
                ''', (playlist_id,))

                row = cursor.fetchone()

            if row:
                return self._row_to_draft(row)

            return None

        except Exception as e:
            logger.error(f"Failed to get draft playlist {playlist_id}: {e}")
            raise

    async def get_device_drafts(self, device_id: str, include_spotify: bool = True) -> List[PlaylistDraft]:
        """Get all drafts for a device."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if include_spotify:
                    cursor.execute('''
                        SELECT id, device_id, session_id, prompt, songs_json, created_at, updated_at, refinements_used, status, spotify_playlist_id
                        FROM playlist_drafts 
                        WHERE device_id = ?
                        ORDER BY updated_at DESC
                    ''', (device_id,))

                else:
                    cursor.execute('''
                        SELECT id, device_id, session_id, prompt, songs_json, created_at, updated_at, refinements_used, status, spotify_playlist_id
                        FROM playlist_drafts 
                        WHERE device_id = ? AND status = 'draft'
                        ORDER BY updated_at DESC
                    ''', (device_id,))

                rows = cursor.fetchall()

            return [self._row_to_draft(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get drafts for device {device_id}: {e}")
            raise

    async def get_user_drafts(self, user_id: str, device_id: str = None, session_id: str = None, include_spotify: bool = True) -> List[PlaylistDraft]:
        """Get all drafts for a user across all their devices and sessions."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT DISTINCT device_id, session_id FROM auth_sessions 
                    WHERE spotify_user_id = ?
                ''', (user_id,))

                user_identifiers = cursor.fetchall()
                device_ids = list(set([row[0] for row in user_identifiers if row[0]]))
                session_ids = list(set([row[1] for row in user_identifiers if row[1]]))

                if device_id and device_id not in device_ids:
                    device_ids.append(device_id)

                if session_id and session_id not in session_ids:
                    session_ids.append(session_id)

                if not device_ids and not session_ids:
                    return []

                conditions = []
                params = []

                if device_ids:
                    placeholders = ','.join(['?' for _ in device_ids])
                    conditions.append(f"device_id IN ({placeholders})")
                    params.extend(device_ids)

                if session_ids:
                    placeholders = ','.join(['?' for _ in session_ids])
                    conditions.append(f"session_id IN ({placeholders})")
                    params.extend(session_ids)

                if not conditions:
                    return []

                where_clause = " OR ".join(conditions)

                if not include_spotify:
                    where_clause = f"({where_clause}) AND status = 'draft'"

                cursor.execute(f'''
                    SELECT id, device_id, session_id, prompt, songs_json, created_at, 
                    updated_at, refinements_used, status, spotify_playlist_id
                    FROM playlist_drafts 
                    WHERE {where_clause}
                    ORDER BY updated_at DESC
                ''', params)

                rows = cursor.fetchall()

            return [self._row_to_draft(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get drafts for user {user_id}: {e}")
            raise

    async def delete_draft(self, playlist_id: str) -> bool:
        """Delete a draft playlist."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    DELETE FROM playlist_drafts 
                    WHERE id = ? AND status = 'draft'
                ''', (playlist_id,))

                success = cursor.rowcount > 0
                conn.commit()

            if success:
                logger.info(f"Deleted draft playlist {playlist_id}")

            else:
                logger.warning(f"Failed to delete draft playlist {playlist_id} - not found or not draft")

            return success

        except Exception as e:
            logger.error(f"Failed to delete draft playlist {playlist_id}: {e}")
            raise

    async def get_spotify_playlist_refinement_count(self, spotify_playlist_id: str) -> int:
        """Get the refinement count for a Spotify playlist."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                select_refinements_sql = f'''
                    SELECT refinements_used FROM {AppConstants.SPOTIFY_PLAYLISTS_TABLE} 
                    WHERE spotify_playlist_id = ?
                '''

                cursor.execute(select_refinements_sql, (spotify_playlist_id,))
                row = cursor.fetchone()

                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to get refinement count for Spotify playlist {spotify_playlist_id}: {e}")
            return 0

    async def update_spotify_playlist_refinement_count(self, spotify_playlist_id: str, refinements_used: int) -> bool:
        """Update the refinement count for a Spotify playlist."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                update_refinements_sql = f'''
                    UPDATE {AppConstants.SPOTIFY_PLAYLISTS_TABLE} 
                    SET refinements_used = ?, updated_at = ?
                    WHERE spotify_playlist_id = ?
                '''

                cursor.execute(update_refinements_sql, (refinements_used, datetime.now(), spotify_playlist_id))
                success = cursor.rowcount > 0
                conn.commit()

                return success

        except Exception as e:
            logger.error(f"Failed to update refinement count for Spotify playlist {spotify_playlist_id}: {e}")
            return False

    async def remove_spotify_playlist_tracking(self, spotify_playlist_id: str) -> bool:
        """Remove a Spotify playlist from our tracking database."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                delete_playlist_sql = f'''
                    DELETE FROM {AppConstants.SPOTIFY_PLAYLISTS_TABLE} 
                    WHERE spotify_playlist_id = ?
                '''

                cursor.execute(delete_playlist_sql, (spotify_playlist_id,))
                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Removed tracking for Spotify playlist {spotify_playlist_id}")

                else:
                    logger.warning(f"Spotify playlist {spotify_playlist_id} not found in tracking")

                return success

        except Exception as e:
            logger.error(f"Failed to remove tracking for Spotify playlist {spotify_playlist_id}: {e}")
            return False

    def _row_to_draft(self, row) -> PlaylistDraft:
        """Convert database row to PlaylistDraft object."""

        songs_json_data = row[4]

        if songs_json_data is None or songs_json_data == '':
            logger.warning(f"Found draft with NULL/empty songs_json: {row[0]}")
            songs = []

        else:
            try:
                songs_data = json.loads(songs_json_data)
                songs = [Song(**song_data) for song_data in songs_data]

            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse songs_json for draft {row[0]}: {e}")
                songs = []

        status = row[8] if row[8] is not None else 'draft'

        return PlaylistDraft(
            id=row[0],
            device_id=row[1],
            session_id=row[2],
            prompt=row[3],
            songs=songs,
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
            refinements_used=row[7] if row[7] is not None else 0,
            status=status,
            spotify_playlist_id=row[9]
        )

    def is_ready(self) -> bool:
        """Check if the service is ready."""

        return self._initialized

    async def cleanup(self):
        """Clean up the service."""

        if self._cleanup_task:
            self._cleanup_task.cancel()

            try:
                await self._cleanup_task

            except asyncio.CancelledError:
                pass

        logger.info("Playlist draft service cleaned up")

playlist_draft_service = PlaylistDraftService()
