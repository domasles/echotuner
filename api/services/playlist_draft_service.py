"""Playlist draft management service for EchoTuner."""

import sqlite3
import uuid
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from core.models import PlaylistDraft, Song
from config.settings import settings

logger = logging.getLogger(__name__)

class PlaylistDraftService:
    """Service for managing playlist drafts and Spotify playlist integration."""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent / settings.DATABASE_FILENAME
        self._initialized = False
        self._cleanup_task = None

    async def initialize(self):
        """Initialize the playlist draft service."""
        try:
            await self._init_database()
            await self._start_cleanup_task()
            self._initialized = True
            logger.info("Playlist draft service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize playlist draft service: {e}")
            raise

    async def _init_database(self):
        """Initialize database tables for playlist drafts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create playlist drafts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS playlist_drafts (
                        id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        session_id TEXT,
                        prompt TEXT NOT NULL,
                        songs TEXT NOT NULL,  -- JSON array of songs
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        refinements_used INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        spotify_playlist_id TEXT,
                        spotify_playlist_url TEXT
                    )
                ''')
                
                # Create table to track Spotify playlists created by EchoTuner
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS echotuner_spotify_playlists (
                        spotify_playlist_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        session_id TEXT,
                        original_draft_id TEXT,
                        playlist_name TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (original_draft_id) REFERENCES playlist_drafts (id)
                    )
                ''')
                
                # Create index for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_playlist_drafts_device_id 
                    ON playlist_drafts(device_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_playlist_drafts_status 
                    ON playlist_drafts(status)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_echotuner_spotify_playlists_user_id 
                    ON echotuner_spotify_playlists(user_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_echotuner_spotify_playlists_device_id 
                    ON echotuner_spotify_playlists(device_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_playlist_drafts_created_at 
                    ON playlist_drafts(created_at)
                ''')
                
                conn.commit()
                logger.debug("Playlist drafts database tables initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize playlist drafts database: {e}")
            raise

    async def _start_cleanup_task(self):
        """Start the background cleanup task for expired drafts."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_drafts_loop())

    async def _cleanup_expired_drafts_loop(self):
        """Background task to clean up expired drafts."""
        while True:
            try:
                await asyncio.sleep(settings.DRAFT_CLEANUP_INTERVAL_HOURS * 3600)
                await self._cleanup_expired_drafts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _cleanup_expired_drafts(self):
        """Remove expired draft playlists."""
        try:
            cutoff_date = datetime.now() - timedelta(days=settings.DRAFT_STORAGE_DAYS)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Only clean up drafts, not playlists added to Spotify
                cursor.execute('''
                    DELETE FROM playlist_drafts 
                    WHERE status = 'draft' AND created_at < ?
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired draft playlists")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired drafts: {e}")

    async def save_draft(self, device_id: str, session_id: Optional[str], prompt: str, 
                        songs: List[Song], refinements_used: int = 0) -> str:
        """Save a playlist as a draft."""
        try:
            playlist_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Convert songs to JSON
            songs_json = [song.model_dump() for song in songs]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO playlist_drafts 
                    (id, device_id, session_id, prompt, songs, created_at, updated_at, refinements_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (playlist_id, device_id, session_id, prompt, 
                     json.dumps(songs_json), now, now, refinements_used))
                
                conn.commit()
                
            logger.info(f"Saved draft playlist {playlist_id} for device {device_id}")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Failed to save draft playlist: {e}")
            raise

    async def update_draft(self, playlist_id: str, songs: List[Song], 
                          refinements_used: int, prompt: Optional[str] = None) -> bool:
        """Update an existing draft playlist."""
        try:
            songs_json = [song.model_dump() for song in songs]
            now = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if prompt:
                    cursor.execute('''
                        UPDATE playlist_drafts 
                        SET songs = ?, refinements_used = ?, updated_at = ?, prompt = ?
                        WHERE id = ? AND status = 'draft'
                    ''', (json.dumps(songs_json), refinements_used, now, prompt, playlist_id))
                else:
                    cursor.execute('''
                        UPDATE playlist_drafts 
                        SET songs = ?, refinements_used = ?, updated_at = ?
                        WHERE id = ? AND status = 'draft'
                    ''', (json.dumps(songs_json), refinements_used, now, playlist_id))
                
                success = cursor.rowcount > 0
                conn.commit()
                
            if success:
                logger.info(f"Updated draft playlist {playlist_id}")
            else:
                logger.warning(f"Failed to update draft playlist {playlist_id} - not found or not draft")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to update draft playlist {playlist_id}: {e}")
            raise

    async def mark_as_added_to_spotify(self, playlist_id: str, spotify_playlist_id: str, 
                                     spotify_url: str, user_id: str = None, device_id: str = None, 
                                     session_id: str = None, playlist_name: str = None) -> bool:
        """Mark a draft as added to Spotify and record the Spotify playlist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the draft status
                cursor.execute('''
                    UPDATE playlist_drafts 
                    SET status = 'added_to_spotify', 
                        spotify_playlist_id = ?, 
                        spotify_playlist_url = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (spotify_playlist_id, spotify_url, datetime.now(), playlist_id))
                
                success = cursor.rowcount > 0
                
                # Record the Spotify playlist in our tracking table
                if success and user_id and device_id and playlist_name:
                    cursor.execute('''
                        INSERT OR REPLACE INTO echotuner_spotify_playlists 
                        (spotify_playlist_id, user_id, device_id, session_id, original_draft_id, 
                         playlist_name, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (spotify_playlist_id, user_id, device_id, session_id, playlist_id, 
                          playlist_name, datetime.now()))
                
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
                
                cursor.execute('''
                    SELECT spotify_playlist_id 
                    FROM echotuner_spotify_playlists 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
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
                    SELECT id, device_id, session_id, prompt, songs, created_at, 
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
                        SELECT id, device_id, session_id, prompt, songs, created_at, 
                               updated_at, refinements_used, status, spotify_playlist_id
                        FROM playlist_drafts 
                        WHERE device_id = ?
                        ORDER BY updated_at DESC
                    ''', (device_id,))
                else:
                    cursor.execute('''
                        SELECT id, device_id, session_id, prompt, songs, created_at, 
                               updated_at, refinements_used, status, spotify_playlist_id
                        FROM playlist_drafts 
                        WHERE device_id = ? AND status = 'draft'
                        ORDER BY updated_at DESC
                    ''', (device_id,))
                
                rows = cursor.fetchall()
                
            return [self._row_to_draft(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get drafts for device {device_id}: {e}")
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

    def _row_to_draft(self, row) -> PlaylistDraft:
        """Convert database row to PlaylistDraft object."""
        
        songs_data = json.loads(row[4])
        songs = [Song(**song_data) for song_data in songs_data]
        
        return PlaylistDraft(
            id=row[0],
            device_id=row[1],
            session_id=row[2],
            prompt=row[3],
            songs=songs,
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
            refinements_used=row[7],
            status=row[8],
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
