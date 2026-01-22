"""
Spotify Playlist Service.
Spotify playlist creation service for EchoTuner.
"""

import logging

from typing import List, Dict, Any, Optional, Tuple

from async_spotify import SpotifyApiClient, TokenRenewClass
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow

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
        self.api_client: Optional[SpotifyApiClient] = None

    async def _setup_service(self):
        """Initialize the SpotifyPlaylistService."""

        try:
            if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
                logger.warning("Spotify credentials not configured - playlist creation disabled")
                return

            # Create client credentials flow
            auth_flow = ClientCredentialsFlow(
                application_id=settings.SPOTIFY_CLIENT_ID, application_secret=settings.SPOTIFY_CLIENT_SECRET
            )

            # Create API client with automatic token renewal
            self.api_client = SpotifyApiClient(
                authorization_flow=auth_flow, hold_authentication=True, token_renew_instance=TokenRenewClass()
            )

            # Get initial token
            await self.api_client.get_auth_token_with_client_credentials()

            # Create httpx client with connection pooling
            await self.api_client.create_new_client(request_limit=1500, request_timeout=30)

        except Exception as e:
            logger.error(f"Failed to initialize Spotify playlist service: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    def is_ready(self) -> bool:
        """Check if the service is ready."""

        return settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET and self.api_client is not None

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
            if not self.api_client:
                await self._setup_service()
                if not self.api_client:
                    raise Exception("Spotify service not initialized - check credentials")

            # Create auth token for user-specific requests
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Get playlist tracks using async-spotify
            results = await self.api_client.playlists.get_tracks(
                playlist_id=playlist_id, limit=100, auth_token=auth_token
            )

            tracks = results.get("items", [])

            # Handle pagination if needed
            next_url = results.get("next")
            while next_url:
                # For pagination, we need to use offset
                offset = len(tracks)
                results = await self.api_client.playlists.get_tracks(
                    playlist_id=playlist_id, limit=100, offset=offset, auth_token=auth_token
                )
                tracks.extend(results.get("items", []))
                next_url = results.get("next")

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
            if not self.api_client:
                await self._setup_service()
                if not self.api_client:
                    raise Exception("Spotify service not initialized - check credentials")

            # Create auth token for user-specific requests
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Get current user ID
            user_data = await self.api_client.user.me(auth_token=auth_token)
            user_id = user_data["id"]

            # Create playlist using async-spotify
            playlist_info = await self.api_client.playlists.create_playlist(
                user_id=user_id,
                playlist_name=playlist_name,
                description=description if description else AppConstants.DEFAULT_PLAYLIST_DESCRIPTION,
                public=public,
                auth_token=auth_token,
            )

            playlist_id = playlist_info["id"]
            playlist_url = playlist_info["external_urls"]["spotify"]

            # Prepare track URIs
            track_uris = []
            for song in songs:
                if song.spotify_id:
                    track_uris.append(f"spotify:track:{song.spotify_id}")

            # Add tracks in batches
            if track_uris:
                await self._add_tracks_to_playlist(playlist_id, track_uris, auth_token)

            logger.debug(f"Created Spotify playlist {playlist_id} with {len(track_uris)} tracks")
            return playlist_id, playlist_url

        except Exception as e:
            logger.error(f"Failed to create Spotify playlist: {e}")
            raise

    async def _add_tracks_to_playlist(
        self, playlist_id: str, track_uris: List[str], auth_token: SpotifyAuthorisationToken
    ):
        """Add tracks to a Spotify playlist in batches."""

        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i : i + batch_size]

            await self.api_client.playlists.add_tracks(
                playlist_id=playlist_id, spotify_uris=batch, auth_token=auth_token
            )

    async def _clear_playlist_tracks(self, playlist_id: str, auth_token: SpotifyAuthorisationToken):
        """Remove all tracks from a Spotify playlist."""

        try:
            # Get current tracks
            results = await self.api_client.playlists.get_tracks(
                playlist_id=playlist_id, limit=100, auth_token=auth_token
            )

            tracks = results.get("items", [])

            if tracks:
                batch_size = 100
                track_uris = [track["track"]["uri"] for track in tracks if track.get("track")]

                for i in range(0, len(track_uris), batch_size):
                    batch = track_uris[i : i + batch_size]

                    await self.api_client.playlists.remove_tracks(
                        playlist_id=playlist_id, spotify_uris=batch, auth_token=auth_token
                    )

        except Exception as e:
            logger.error(f"Failed to clear playlist tracks: {e}")
            raise

    async def remove_track_from_playlist(self, access_token: str, playlist_id: str, track_uri: str) -> bool:
        """Remove a track from a Spotify playlist."""

        try:
            if not self.api_client:
                await self._setup_service()
                if not self.api_client:
                    raise Exception("Spotify service not initialized - check credentials")

            # Create auth token for user-specific requests
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            await self.api_client.playlists.remove_tracks(
                playlist_id=playlist_id, spotify_uris=[track_uri], auth_token=auth_token
            )

            logger.debug(f"Successfully removed track from playlist {playlist_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing track from playlist: {e}")
            return False

    async def get_playlist_details(self, access_token: str, playlist_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific Spotify playlist including current track count."""

        try:
            if not self.api_client:
                await self._setup_service()
                if not self.api_client:
                    raise Exception("Spotify service not initialized - check credentials")

            # Create auth token for user-specific requests
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Get playlist details using async-spotify
            playlist_data = await self.api_client.playlists.get_one(playlist_id=playlist_id, auth_token=auth_token)

            return {
                "name": playlist_data.get("name"),
                "tracks": {"total": playlist_data.get("tracks", {}).get("total", 0)},
            }

        except Exception as e:
            logger.error(f"Failed to get playlist details for {playlist_id}: {e}")
            raise

    async def close(self):
        """Close the Spotify API client."""

        if self.api_client:
            await self.api_client.close_client()
            logger.debug("Closed Spotify playlist service client")


spotify_playlist_service = SpotifyPlaylistService()
