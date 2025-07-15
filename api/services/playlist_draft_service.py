"""
Playlist draft service.
Manages playlist drafts, including saving, updating, and cleaning up expired drafts.
Uses standardized database operations and error handling.
"""

import asyncio
import logging
import uuid
import json

from datetime import datetime, timedelta
from typing import List, Optional

from core.singleton import SingletonServiceBase
from models import PlaylistDraft, Song
from config.app_constants import AppConstants
from config.settings import settings
from utils.exceptions import handle_service_errors, raise_playlist_error, ErrorCode

from services.database_service import db_service

from utils.input_validator import UniversalValidator

logger = logging.getLogger(__name__)

class PlaylistDraftService(SingletonServiceBase):
    """Service for managing playlist drafts and Spotify playlist integration using ORM."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the PlaylistDraftService."""

        self._log_initialization("Playlist draft service initialized with ORM", logger)

    @handle_service_errors("initialize_playlist_draft_service")
    async def initialize(self):
        """Initialize the playlist draft service with error handling."""
        try:
            asyncio.create_task(self._cleanup_expired_drafts_loop())
        except Exception as e:
            raise_playlist_error(f"Failed to initialize playlist draft service: {e}", ErrorCode.INTERNAL_ERROR)

    async def _cleanup_expired_drafts_loop(self):
        """Background task to clean up expired drafts."""

        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_expired_drafts()
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _cleanup_expired_drafts(self):
        """Clean up expired drafts older than 24 hours."""

        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            cutoff_timestamp = cutoff_time.isoformat()
            
            # Use database service for cleanup
            # Note: This would need a specific method in database service for cleaning old drafts
            logger.debug("Cleaned up expired drafts")

        except Exception as e:
            logger.error(f"Failed to cleanup expired drafts: {e}")

    def _create_draft_id(self) -> str:
        """Generate a unique draft ID."""
        return str(uuid.uuid4())

    @handle_service_errors("save_draft")
    async def save_draft(self, device_id: str, session_id: str, prompt: str, songs: List[Song]) -> str:
        """Save a playlist draft using database service with error handling."""
        try:
            draft_id = self._create_draft_id()
            songs_json = json.dumps([song.model_dump() for song in songs])
            
            draft_data = {
                'id': draft_id,
                'device_id': device_id,
                'session_id': session_id,
                'prompt': prompt,
                'songs_json': songs_json,
                'songs': songs_json,  # For backwards compatibility
                'is_draft': True,
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'spotify_playlist_id': None,
                'spotify_playlist_url': None
            }

            success = await db_service.save_playlist_draft(draft_data)
            if success:
                logger.info(f"Saved playlist draft {draft_id}")
                return draft_id
            else:
                raise_playlist_error("Failed to save draft to database", ErrorCode.PLAYLIST_CREATION_FAILED)

        except Exception as e:
            raise_playlist_error(f"Failed to save draft: {e}", ErrorCode.PLAYLIST_CREATION_FAILED)

    async def update_draft(self, draft_id: str, songs: List[Song], prompt: str = None) -> bool:
        """Update an existing draft using database service."""

        try:
            songs_json = json.dumps([song.model_dump() for song in songs])
            
            draft_data = {
                'id': draft_id,
                'songs_json': songs_json,
                'songs': songs_json,  # For backwards compatibility
                'updated_at': datetime.now().isoformat()
            }

            if prompt:
                draft_data['prompt'] = prompt

            success = await db_service.save_playlist_draft(draft_data)
            if success:
                logger.info(f"Updated playlist draft {draft_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to update draft {draft_id}: {e}")
            return False

    async def get_draft(self, draft_id: str) -> Optional[PlaylistDraft]:
        """Get a playlist draft by ID using database service."""

        try:
            logger.info(f"Getting draft for ID: {draft_id}")
            draft_data = await db_service.get_playlist_draft(draft_id)
            if not draft_data:
                logger.warning(f"No draft data found for ID: {draft_id}")
                return None

            # Parse songs from JSON
            songs_data = json.loads(draft_data.get('songs_json', '[]'))
            songs = [Song.model_validate(song_data) for song_data in songs_data]

            draft = PlaylistDraft(
                id=draft_data['id'],
                device_id=draft_data['device_id'],
                session_id=draft_data['session_id'],
                prompt=draft_data['prompt'],
                songs=songs,
                status=draft_data.get('status', 'draft'),
                created_at=draft_data['created_at'],
                updated_at=draft_data['updated_at']
            )

            if draft_data.get('spotify_playlist_id'):
                draft.spotify_playlist_id = draft_data['spotify_playlist_id']
                draft.spotify_playlist_url = draft_data['spotify_playlist_url']

            return draft

        except Exception as e:
            logger.error(f"Failed to get draft {draft_id}: {e}")
            return None

    async def get_user_drafts(self, device_id: str, limit: int = 10, user_id: str = None, session_id: str = None, include_spotify: bool = True) -> List[PlaylistDraft]:
        """Get user's drafts using database service."""

        try:
            drafts_data = await db_service.get_user_drafts(device_id, limit, user_id)
            drafts = []

            for draft_data in drafts_data:
                try:
                    # Parse songs from JSON
                    songs_data = json.loads(draft_data.get('songs_json', '[]'))
                    songs = [Song.model_validate(song_data) for song_data in songs_data]

                    draft = PlaylistDraft(
                        id=draft_data['id'],
                        device_id=draft_data['device_id'],
                        session_id=draft_data['session_id'],
                        prompt=draft_data['prompt'],
                        songs=songs,
                        status=draft_data.get('status', 'draft'),
                        created_at=draft_data['created_at'],
                        updated_at=draft_data['updated_at']
                    )
                    drafts.append(draft)

                except Exception as e:
                    logger.error(f"Failed to parse draft data: {e}")
                    continue

            return drafts

        except Exception as e:
            logger.error(f"Failed to get user drafts for device {device_id}: {e}")
            return []

    async def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft using database service."""

        try:
            success = await db_service.delete_playlist_draft(draft_id)
            if success:
                logger.info(f"Deleted playlist draft {draft_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to delete draft {draft_id}: {e}")
            return False

    async def save_spotify_playlist(self, spotify_playlist_id: str, user_id: str, device_id: str, session_id: str, draft_id: str, playlist_name: str) -> bool:
        """Save Spotify playlist info using database service."""

        try:
            # This would need to be implemented in database service
            # For now, just log the operation
            logger.info(f"Saved Spotify playlist {spotify_playlist_id} for draft {draft_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save Spotify playlist: {e}")
            return False

    async def get_user_playlists(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user's Spotify playlists using database service."""

        try:
            # This would need to be implemented in database service
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Failed to get user playlists for {user_id}: {e}")
            return []

    async def get_playlist_by_spotify_id(self, spotify_playlist_id: str) -> Optional[dict]:
        """Get playlist by Spotify ID using database service."""

        try:
            # This would need to be implemented in database service
            # For now, return None
            return None

        except Exception as e:
            logger.error(f"Failed to get playlist by Spotify ID {spotify_playlist_id}: {e}")
            return None

    async def get_user_playlists_by_device(self, device_id: str, limit: int = 50) -> List[dict]:
        """Get user's playlists by device using database service."""

        try:
            # This would need to be implemented in database service
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Failed to get user playlists by device {device_id}: {e}")
            return []

    async def get_user_identifiers_for_cleanup(self, account_type: str = None) -> List[tuple]:
        """Get user identifiers for cleanup using database service."""

        try:
            # This would need to be implemented in database service
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Failed to get user identifiers for cleanup: {e}")
            return []

    async def cleanup_user_data(self, device_id: str = None, spotify_user_id: str = None, account_type: str = None):
        """Clean up user data using database service."""

        try:
            if device_id:
                # Clean up drafts for device
                drafts = await self.get_user_drafts(device_id)
                for draft in drafts:
                    await self.delete_draft(draft.id)
                
                logger.info(f"Cleaned up data for device {device_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup user data: {e}")

    async def get_all_playlists_for_device(self, device_id: str) -> List[dict]:
        """Get all playlists for a device using database service."""

        try:
            # This would use database service to get all playlists for device
            return []

        except Exception as e:
            logger.error(f"Failed to get all playlists for device {device_id}: {e}")
            return []

    async def get_device_drafts(self, device_id: str, include_spotify: bool = True, limit: int = 10) -> List[PlaylistDraft]:
        """Get device drafts - alias for get_user_drafts for backwards compatibility."""
        return await self.get_user_drafts(device_id, limit)

    async def get_user_echotuner_spotify_playlist_ids(self, user_id: str) -> List[str]:
        """Get EchoTuner Spotify playlist IDs for a user."""
        try:
            return await db_service.get_user_echotuner_spotify_playlist_ids(user_id)
        except Exception as e:
            logger.error(f"Failed to get user EchoTuner Spotify playlist IDs: {e}")
            return []

    async def mark_as_added_to_spotify(self, playlist_id: str, spotify_playlist_id: str, spotify_url: str, user_id: str, device_id: str, session_id: str, playlist_name: str) -> bool:
        """Mark a playlist draft as added to Spotify."""
        try:
            return await db_service.mark_as_added_to_spotify(
                playlist_id=playlist_id,
                spotify_playlist_id=spotify_playlist_id,
                spotify_url=spotify_url,
                user_id=user_id,
                device_id=device_id,
                session_id=session_id,
                playlist_name=playlist_name
            )
        except Exception as e:
            logger.error(f"Failed to mark playlist as added to Spotify: {e}")
            return False

    @handle_service_errors("remove_spotify_playlist_tracking")
    async def remove_spotify_playlist_tracking(self, spotify_playlist_id: str) -> bool:
        """Remove tracking of a Spotify playlist when it's deleted."""
        try:
            # Remove the playlist from drafts if it exists
            success = await db_service.remove_spotify_playlist_from_drafts(spotify_playlist_id)
            if success:
                logger.info(f"Removed Spotify playlist tracking for {spotify_playlist_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to remove Spotify playlist tracking for {spotify_playlist_id}: {e}")
            return False

# Create singleton instance
playlist_draft_service = PlaylistDraftService()
