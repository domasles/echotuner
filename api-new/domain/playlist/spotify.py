"""
Spotify Playlist Service.
Spotify playlist creation service for EchoTuner.
"""

import aiohttp
import asyncio
import logging

from typing import List, Dict, Any, Optional, Tuple

from application.core.singleton import SingletonServiceBase
from application import Song

from infrastructure.config.app_constants import AppConstants
from infrastructure.config.settings import settings

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class SpotifyPlaylistService(SingletonServiceBase):
    """Service for creating playlists in Spotify."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the SpotifyPlaylistService."""

        self._log_initialization("Spotify playlist service initialized successfully", logger)

    async def initialize(self):
        """Initialize the Spotify playlist service."""

        try:
            if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
                logger.warning("Spotify credentials not configured - playlist creation disabled")
                return

        except Exception as e:
            logger.error(f"Failed to initialize Spotify playlist service: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    def is_ready(self) -> bool:
        """Check if the service is ready."""

        return settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET

    async def get_user_playlists(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's Spotify playlists."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {access_token}'}

                url = 'https://api.spotify.com/v1/me/playlists'
                params = {'limit': 50}

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])

                    elif response.status == 401:
                        raise Exception("Invalid or expired access token")

                    else:
                        raise Exception(f"Failed to fetch playlists: {response.status}")

        except Exception as e:
            logger.error(f"Failed to get user playlists: {e}")
            raise

    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a specific Spotify playlist."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {access_token}'}

                url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
                params = {'limit': 100}

                tracks = []

                while url:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            tracks.extend(data.get('items', []))
                            url = data.get('next')
                            params = {}

                        elif response.status == 401:
                            raise Exception("Invalid or expired access token")

                        else:
                            raise Exception(f"Failed to fetch playlist tracks: {response.status}")

                return tracks

        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {e}")
            raise

    async def create_playlist(self, access_token: str, playlist_name: str, songs: List[Song], description: Optional[str] = None, public: bool = False) -> Tuple[str, str]:
        """Create a new Spotify playlist with the given songs."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }

                user_id = await self._get_user_id(session, headers)

                playlist_data = {
                    'name': playlist_name,
                    'description': description if description else AppConstants.DEFAULT_PLAYLIST_DESCRIPTION,
                    'public': public
                }

                url = f'https://api.spotify.com/v1/users/{user_id}/playlists'

                async with session.post(url, headers=headers, json=playlist_data) as response:
                    if response.status == 201:
                        playlist_info = await response.json()
                        playlist_id = playlist_info['id']
                        playlist_url = playlist_info['external_urls']['spotify']

                    elif response.status == 401:
                        raise Exception("Invalid or expired access token")

                    else:
                        raise Exception(f"Failed to create playlist: {response.status}")

                track_uris = []

                for song in songs:
                    if song.spotify_id:
                        track_uris.append(f'spotify:track:{song.spotify_id}')

                if track_uris:
                    await self._add_tracks_to_playlist(session, headers, playlist_id, track_uris)

                logger.debug(f"Created Spotify playlist {playlist_id} with {len(track_uris)} tracks")
                return playlist_id, playlist_url

        except Exception as e:
            logger.error(f"Failed to create Spotify playlist: {e}")
            raise

    async def _get_user_id(self, session: aiohttp.ClientSession, headers: Dict[str, str]) -> str:
        """Get the current user's Spotify ID."""

        url = 'https://api.spotify.com/v1/me'

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                user_data = await response.json()
                return user_data['id']

            elif response.status == 401:
                raise Exception("Invalid or expired access token")

            else:
                raise Exception(f"Failed to get user ID: {response.status}")

    async def _add_tracks_to_playlist(self, session: aiohttp.ClientSession, headers: Dict[str, str], playlist_id: str, track_uris: List[str]):
        """Add tracks to a Spotify playlist."""

        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]

            url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            data = {'uris': batch}

            async with session.post(url, headers=headers, json=data) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"Failed to add tracks to playlist: {response.status}")

            if i + batch_size < len(track_uris):
                await asyncio.sleep(0.1)

    async def _clear_playlist_tracks(self, session: aiohttp.ClientSession, headers: Dict[str, str], playlist_id: str):
        """Remove all tracks from a Spotify playlist."""

        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                tracks = data.get('items', [])

                if tracks:
                    batch_size = 100
                    track_uris = [{'uri': track['track']['uri']} for track in tracks if track.get('track')]

                    for i in range(0, len(track_uris), batch_size):
                        batch = track_uris[i:i + batch_size]

                        delete_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
                        delete_data = {'tracks': batch}

                        async with session.delete(delete_url, headers=headers, json=delete_data) as delete_response:
                            if delete_response.status not in [200, 201]:
                                raise Exception(f"Failed to clear playlist tracks: {delete_response.status}")

                        if i + batch_size < len(track_uris):
                            await asyncio.sleep(0.1)

            elif response.status == 401:
                raise Exception("Invalid or expired access token")

            else:
                raise Exception(f"Failed to get playlist tracks: {response.status}")

    async def get_playlist_details(self, access_token: str, playlist_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific Spotify playlist including current track count."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {access_token}'}
                url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
                params = {'fields': 'id,name,description,tracks.total,external_urls,images'}

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 401:
                        raise Exception("Invalid or expired access token")

                    elif response.status == 404:
                        raise Exception("Playlist not found")

                    else:
                        raise Exception(f"Failed to fetch playlist details: {response.status}")

        except Exception as e:
            logger.error(f"Failed to get playlist details for {playlist_id}: {e}")
            raise

    async def remove_track_from_playlist(self, access_token: str, playlist_id: str, track_uri: str) -> bool:
        """Remove a track from a Spotify playlist."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }

                url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
                data = {
                    'tracks': [{'uri': track_uri}]
                }

                async with session.delete(url, headers=headers, json=data) as response:
                    if response.status in [200, 201]:
                        logger.debug(f"Successfully removed track from playlist {playlist_id}")
                        return True

                    else:
                        logger.error(f"Failed to remove track: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error removing track from playlist: {e}")
            return False

spotify_playlist_service = SpotifyPlaylistService()
