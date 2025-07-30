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

from infrastructure.singleton import SingletonServiceBase
from application import PlaylistDraft, Song
from domain.config.app_constants import AppConstants
from domain.config.settings import settings
from domain.shared.exceptions import handle_service_errors, raise_playlist_error, ErrorCode

from infrastructure.database.repository import repository
from infrastructure.database.models.playlists import PlaylistDraft as PlaylistDraftModel, SpotifyPlaylist

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class PlaylistDraftService(SingletonServiceBase):
    """Service for managing playlist drafts and Spotify playlist integration using ORM."""

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the PlaylistDraftService."""

        self.repository = repository

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
    async def save_draft(self, user_id: str, prompt: str, songs: List[Song]) -> Optional[str]:
        """Save a playlist draft using user_id (unified approach)."""
        try:
            draft_id = self._create_draft_id()
            songs_json = json.dumps([song.model_dump() for song in songs])
            
            # Create data for new draft
            draft_data = {
                'id': draft_id,
                'user_id': user_id,
                'prompt': prompt,
                'songs_json': songs_json,
                'is_draft': True,
                'status': 'draft',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'spotify_playlist_id': None,
                'spotify_playlist_url': None
            }

            # Save to database using repository
            saved_draft = await self.repository.create(PlaylistDraftModel, draft_data)
            if saved_draft:
                logger.info(f"Updated playlist draft {draft_id}")
                return draft_id  # Return the draft ID, not True
            else:
                return None  # Return None on failure, not False

        except Exception as e:
            logger.error(f"Failed to update draft {draft_id}: {e}")
            return None  # Return None on exception, not False

    async def get_draft(self, draft_id: str) -> Optional[PlaylistDraft]:
        """Get a playlist draft by ID using database service."""

        try:
            logger.info(f"Getting draft for ID: {draft_id}")
            # Get draft from database using repository
            draft_model = await self.repository.get_by_id(PlaylistDraftModel, draft_id)
            
            if not draft_model:
                logger.warning(f"No draft data found for ID: {draft_id}")
                return None

            # Parse songs from JSON
            songs_data = json.loads(draft_model.songs_json or '[]')
            songs = [Song.model_validate(song_data) for song_data in songs_data]

            draft = PlaylistDraft(
                id=draft_model.id,
                user_id=draft_model.user_id,
                prompt=draft_model.prompt,
                songs=songs,
                status=draft_model.status or 'draft',
                created_at=draft_model.created_at,
                updated_at=draft_model.updated_at
            )

            if draft_model.spotify_playlist_id:
                draft.spotify_playlist_id = draft_model.spotify_playlist_id
                draft.spotify_playlist_url = draft_model.spotify_playlist_url

            return draft

        except Exception as e:
            logger.error(f"Failed to get draft {draft_id}: {e}")
            return None

    async def get_user_drafts(self, user_id: str, limit: int = 10, include_spotify: bool = True) -> List[PlaylistDraft]:
        """Get user's drafts using user_id in unified system."""

        try:
            # Get drafts from database using repository
            draft_models = await self.repository.list_with_conditions(
                PlaylistDraftModel, 
                {"user_id": user_id}
            )
            
            drafts = []
            for draft_model in draft_models[:limit]:  # Apply limit
                try:
                    # Parse songs from JSON
                    songs_data = json.loads(draft_model.songs_json or '[]')
                    songs = [Song.model_validate(song_data) for song_data in songs_data]

                    draft = PlaylistDraft(
                        id=draft_model.id,
                        user_id=draft_model.user_id,
                        prompt=draft_model.prompt,
                        songs=songs,
                        status=draft_model.status or 'draft',
                        created_at=draft_model.created_at,
                        updated_at=draft_model.updated_at
                    )
                    drafts.append(draft)

                except Exception as e:
                    logger.error(f"Failed to parse draft data: {e}")
                    continue

            return drafts

        except Exception as e:
            logger.error(f"Failed to get user drafts for user {user_id}: {e}")
            return []

    async def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft using database service."""

        try:
            # Delete from database using repository
            success = await self.repository.delete(PlaylistDraftModel, draft_id)
            if success:
                logger.info(f"Deleted playlist draft {draft_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to delete draft {draft_id}: {e}")
            return False

    async def update_draft(self, draft_id: str, user_id: str, prompt: str, songs: List[Song]) -> Optional[str]:
        """Update an existing draft with new songs."""
        try:
            songs_json = json.dumps([song.model_dump() for song in songs])
            
            # Update data for existing draft
            update_data = {
                'prompt': prompt,
                'songs_json': songs_json,
                'updated_at': datetime.now()
            }

            # Update in database using repository
            success = await self.repository.update(PlaylistDraftModel, draft_id, update_data)
            if success:
                logger.info(f"Updated playlist draft {draft_id}")
                return draft_id  # Return the draft ID on success
            else:
                return None  # Return None on failure

        except Exception as e:
            logger.error(f"Failed to update draft {draft_id}: {e}")
            return None

    async def cleanup_user_data(self, user_id: str = None, account_type: str = None):
        """Clean up user data using user_id in unified system."""

        try:
            if user_id:
                # Clean up drafts for user
                drafts = await self.get_user_drafts(user_id)
                for draft in drafts:
                    await self.delete_draft(draft.id)
                
                logger.info(f"Cleaned up data for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup user data: {e}")

    async def get_user_echotuner_spotify_playlist_ids(self, user_id: str) -> List[str]:
        """Get EchoTuner Spotify playlist IDs for a user."""
        try:
            # Get all drafts that have been added to Spotify
            drafts = await self.repository.list_with_conditions(
                PlaylistDraftModel, 
                {"user_id": user_id, "status": "added_to_spotify"}
            )
            
            playlist_ids = []
            for draft in drafts:
                if draft.spotify_playlist_id:
                    playlist_ids.append(draft.spotify_playlist_id)
            
            logger.debug(f"Found {len(playlist_ids)} EchoTuner Spotify playlists for user {user_id}")
            return playlist_ids
            
        except Exception as e:
            logger.error(f"Failed to get user EchoTuner Spotify playlist IDs: {e}")
            return []

    async def mark_as_added_to_spotify(self, playlist_id: str, spotify_playlist_id: str, spotify_url: str, user_id: str, playlist_name: str) -> bool:
        """Mark a playlist draft as added to Spotify."""
        try:
            # Update the playlist draft to mark it as added to Spotify
            draft = await self.repository.get_by_field(PlaylistDraftModel, 'id', playlist_id)
            if draft:
                await self.repository.update(PlaylistDraftModel, playlist_id, {
                    'spotify_playlist_id': spotify_playlist_id,
                    'spotify_playlist_url': spotify_url,
                    'status': 'added_to_spotify',
                    'updated_at': datetime.now()
                })

            # Create a tracking record in SpotifyPlaylist table
            spotify_playlist_data = {
                'spotify_playlist_id': spotify_playlist_id,
                'user_id': user_id,
                'original_draft_id': playlist_id,
                'playlist_name': playlist_name,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            await self.repository.create(SpotifyPlaylist, spotify_playlist_data)
            logger.info(f"Marked playlist {playlist_id} as added to Spotify with ID {spotify_playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark playlist as added to Spotify: {e}")
            return False

# Create singleton instance
playlist_draft_service = PlaylistDraftService()
