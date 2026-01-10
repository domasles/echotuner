"""
Spotify Playlist Service.
Spotify playlist creation service for EchoTuner.
"""

import httpx
import asyncio
import logging

from typing import List, Dict, Any, Optional, Tuple

from infrastructure.singleton import SingletonServiceBase
from application import Song

from domain.config.app_constants import AppConstants
from domain.config.settings import settings

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)


class SpotifyPlaylistService(SingletonServiceBase):
    """Service for creating playlists in Spotify."""

    def __init__(self):
        super().__init__()
        self._httpx_client: Optional[httpx.AsyncClient] = None

    async def _setup_service(self):
        """Initialize the SpotifyPlaylistService with persistent httpx client."""

        try:
            if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
                logger.warning("Spotify credentials not configured - playlist creation disabled")
                return

            # Create persistent httpx client for connection pooling
            self._httpx_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
            logger.debug("Created persistent httpx client for Spotify service")

        except Exception as e:
            logger.error(f"Failed to initialize Spotify playlist service: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    def is_ready(self) -> bool:
        """Check if the service is ready."""

        return settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET and self._httpx_client is not None

    async def get_user_playlists_from_db(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's Spotify playlists from database instead of Spotify API."""

        from infrastructure.database.repository import repository
        from infrastructure.database.models.playlists import SpotifyPlaylist

        try:
            # Use generic repository method instead of domain-specific
            spotify_playlists = await repository.list_by_field(SpotifyPlaylist, "user_id", user_id)

            # Convert to the expected format
            playlists = []
            for playlist in spotify_playlists:
                playlists.append(
                    {
                        "id": playlist.spotify_playlist_id,
                        "name": playlist.playlist_name,
                        "tracks": {"total": 0},  # Will be updated by get_playlist_details
                        "external_urls": {
                            "spotify": f"https://open.spotify.com/playlist/{playlist.spotify_playlist_id}"
                        },
                    }
                )

            return playlists

        except Exception as e:
            logger.error(f"Failed to get user playlists from DB: {e}")
            return []

    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a specific Spotify playlist."""

        try:
            if not self._httpx_client:
                # Try to reinitialize if client wasn't created
                await self._setup_service()

                if not self._httpx_client:
                    raise Exception("Spotify service not initialized - check credentials")

            headers = {"Authorization": f"Bearer {access_token}"}

            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            params = {"limit": 100}

            tracks = []

            while url:
                response = await self._httpx_client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    tracks.extend(data.get("items", []))
                    url = data.get("next")
                    params = {}

                elif response.status_code == 401:
                    raise Exception("Invalid or expired access token")

                else:
                    raise Exception(f"Failed to fetch playlist tracks: {response.status_code}")

            return tracks

        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {e}")
            raise

    async def create_playlist(
        self,
        access_token: str,
        playlist_name: str,
        songs: List[Song],
        description: Optional[str] = None,
        public: bool = False,
    ) -> Tuple[str, str]:
        """Create a new Spotify playlist with the given songs."""

        try:
            if not self._httpx_client:
                # Try to reinitialize if client wasn't created
                await self._setup_service()

                if not self._httpx_client:
                    raise Exception("Spotify service not initialized - check credentials")

            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            user_id = await self._get_user_id(self._httpx_client, headers)

            playlist_data = {
                "name": playlist_name,
                "description": description if description else AppConstants.DEFAULT_PLAYLIST_DESCRIPTION,
                "public": public,
            }

            url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

            response = await self._httpx_client.post(url, headers=headers, json=playlist_data)

            if response.status_code == 201:
                playlist_info = response.json()
                playlist_id = playlist_info["id"]
                playlist_url = playlist_info["external_urls"]["spotify"]

            elif response.status_code == 401:
                raise Exception("Invalid or expired access token")

            else:
                raise Exception(f"Failed to create playlist: {response.status_code}")

            track_uris = []

            for song in songs:
                if song.spotify_id:
                    track_uris.append(f"spotify:track:{song.spotify_id}")

            if track_uris:
                await self._add_tracks_to_playlist(self._httpx_client, headers, playlist_id, track_uris)

            logger.debug(f"Created Spotify playlist {playlist_id} with {len(track_uris)} tracks")
            return playlist_id, playlist_url

        except Exception as e:
            logger.error(f"Failed to create Spotify playlist: {e}")
            raise

    async def _get_user_id(self, client: httpx.AsyncClient, headers: Dict[str, str]) -> str:
        """Get the current user's Spotify ID."""

        url = "https://api.spotify.com/v1/me"

        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            return user_data["id"]

        elif response.status_code == 401:
            raise Exception("Invalid or expired access token")

        else:
            raise Exception(f"Failed to get user ID: {response.status_code}")

    async def _add_tracks_to_playlist(
        self, client: httpx.AsyncClient, headers: Dict[str, str], playlist_id: str, track_uris: List[str]
    ):
        """Add tracks to a Spotify playlist."""

        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i : i + batch_size]

            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            data = {"uris": batch}

            response = await client.post(url, headers=headers, json=data)
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to add tracks to playlist: {response.status}")

            # No sleep needed - Spotify rate limit is per-user, not global
            # await asyncio.sleep(0.1)

    async def _clear_playlist_tracks(self, client: httpx.AsyncClient, headers: Dict[str, str], playlist_id: str):
        """Remove all tracks from a Spotify playlist."""

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            tracks = data.get("items", [])

            if tracks:
                batch_size = 100
                track_uris = [{"uri": track["track"]["uri"]} for track in tracks if track.get("track")]

                for i in range(0, len(track_uris), batch_size):
                    batch = track_uris[i : i + batch_size]

                    delete_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
                    delete_data = {"tracks": batch}

                    delete_response = await client.delete(delete_url, headers=headers, json=delete_data)

                    if delete_response.status_code not in [200, 201]:
                        raise Exception(f"Failed to clear playlist tracks: {delete_response.status_code}")

                    # No sleep needed - Spotify rate limit is per-user, not global
                    # await asyncio.sleep(0.1)

        elif response.status_code == 401:
            raise Exception("Invalid or expired access token")

        else:
            raise Exception(f"Failed to get playlist tracks: {response.status_code}")

    async def remove_track_from_playlist(self, access_token: str, playlist_id: str, track_uri: str) -> bool:
        """Remove a track from a Spotify playlist."""

        try:
            if not self._httpx_client:
                # Try to reinitialize if client wasn't created
                await self._setup_service()

                if not self._httpx_client:
                    raise Exception("Spotify service not initialized - check credentials")

            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            data = {"tracks": [{"uri": track_uri}]}

            response = await self._httpx_client.delete(url, headers=headers, json=data)

            if response.status_code in [200, 201]:
                logger.debug(f"Successfully removed track from playlist {playlist_id}")
                return True

            else:
                logger.error(f"Failed to remove track: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error removing track from playlist: {e}")
            return False

    async def get_playlist_details(self, access_token: str, playlist_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific Spotify playlist including current track count."""

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}"}
                url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
                params = {"fields": "name,tracks.total"}

                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    raise Exception("Invalid or expired access token")

                elif response.status_code == 404:
                    raise Exception("Playlist not found")

                else:
                    raise Exception(f"Failed to fetch playlist details: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to get playlist details for {playlist_id}: {e}")
            raise


spotify_playlist_service = SpotifyPlaylistService()
