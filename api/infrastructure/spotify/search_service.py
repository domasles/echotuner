"""
Spotify search service.
Searches for songs in real-time using the Spotify Web API with async-spotify.
Fast song verification and metadata retrieval for AI-generated suggestions.
"""

import logging
import asyncio
from typing import List, Optional

from async_spotify import SpotifyApiClient, TokenRenewClass
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow

from infrastructure.singleton import SingletonServiceBase
from application import Song, UserContext
from domain.config.settings import settings

logger = logging.getLogger(__name__)


class SpotifySearchService(SingletonServiceBase):
    """Service for searching songs in real-time using Spotify Web API with async-spotify."""

    def __init__(self):
        super().__init__()
        self.api_client: Optional[SpotifyApiClient] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None

    async def _setup_service(self):
        """Initialize the SpotifySearchService with async-spotify."""

        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET

        try:
            if not self.client_id or not self.client_secret:
                logger.error("Spotify credentials not found")
                raise RuntimeError(
                    "Spotify credentials are required. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables."
                )

            # Create client credentials flow
            auth_flow = ClientCredentialsFlow(application_id=self.client_id, application_secret=self.client_secret)

            # Create API client with automatic token renewal
            self.api_client = SpotifyApiClient(
                authorization_flow=auth_flow, hold_authentication=True, token_renew_instance=TokenRenewClass()
            )

            # Get initial token
            await self.api_client.get_auth_token_with_client_credentials()

            # Create httpx client with connection pooling
            await self.api_client.create_new_client(request_limit=1500, request_timeout=30)  # Max concurrent requests

            # Test connection
            await self._test_connection()

            logger.debug("SpotifySearchService initialized with async-spotify")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Failed to initialize Spotify Search Service: {e}")
            logger.error("Full traceback:", exc_info=True)
            raise RuntimeError(f"Spotify Search Service initialization failed: {str(e)}")

    async def _ensure_valid_token(self):
        """Ensure the client credentials token is valid and refresh if needed"""

        try:
            # Refresh the client credentials token
            await self.api_client.get_auth_token_with_client_credentials()
            logger.debug("Refreshed Spotify client credentials token")

        except Exception as e:
            logger.error(f"Failed to refresh Spotify token: {e}")
            raise

    async def _test_connection(self):
        """Test Spotify API connection"""

        try:
            # Search for a test track
            results = await self.api_client.search.start(query="test", query_type=["track"], limit=1)

            if not results or not results.get("tracks"):
                raise Exception("Invalid API response")

            logger.debug("Spotify API connection test successful")

        except Exception as e:
            logger.error(f"Spotify API test failed: {e}")
            raise Exception(f"Spotify API test failed: {str(e)}")

    async def _search_spotify(self, query: str, limit: int = None) -> List[Song]:
        """Perform actual Spotify search using async-spotify"""

        if limit is None:
            limit = settings.MAX_SONGS_PER_PLAYLIST // 3

        try:
            if not self.api_client:
                raise RuntimeError("Spotify API client not initialized")

            # Ensure we have a valid client credentials token
            await self._ensure_valid_token()

            # Perform search
            results = await self.api_client.search.start(query=query, query_type=["track"], limit=limit)

            # Add null safety checks
            if not results or not results.get("tracks") or not results["tracks"].get("items"):
                logger.warning(f"Spotify search returned no results for query: {query}")
                return []

            songs = []

            for track in results["tracks"]["items"]:
                song = Song(
                    title=track["name"],
                    artist=", ".join([artist["name"] for artist in track["artists"]]),
                    album=track["album"]["name"],
                    spotify_id=track["id"],
                    duration_ms=track.get("duration_ms"),
                    popularity=track.get("popularity", 50),
                )

                songs.append(song)

            return songs

        except Exception as e:
            logger.error(f"Spotify search error for '{query}': {e}")
            raise RuntimeError(f"Spotify search error for '{query}': {str(e)}")

    async def get_followed_artists(self, access_token: str, limit: int = 50) -> List[dict]:
        """Get user's followed artists using access token"""

        try:
            if not self.api_client:
                raise RuntimeError("Spotify API client not initialized")

            # Create auth token for user-specific requests
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Get followed artists
            results = await self.api_client.follow.get_following(item_type="artist", limit=limit, auth_token=auth_token)

            artists = results.get("artists", {}).get("items", [])
            logger.debug(f"Retrieved {len(artists)} followed artists")

            return artists

        except Exception as e:
            logger.error(f"Failed to get followed artists: {e}")
            return []

    async def get_user_top_artists(
        self, access_token: str, time_range: str = "medium_term", limit: int = 20
    ) -> List[dict]:
        """Get user's top artists from listening history using access_token"""

        try:
            if not self.api_client:
                raise RuntimeError("Spotify API client not initialized")

            # Create auth token
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Get top artists
            results = await self.api_client.personalization.get_top_artists(
                time_range=time_range, limit=limit, auth_token=auth_token
            )

            artists = results.get("items", [])
            logger.debug(f"Retrieved {len(artists)} top artists for time range: {time_range}")

            return artists

        except Exception as e:
            logger.error(f"Failed to get top artists: {e}")
            return []

    async def search_artists(self, access_token: str, query: str, limit: int = 20) -> List[dict]:
        """Search for artists using access token"""

        try:
            if not self.api_client:
                raise RuntimeError("Spotify API client not initialized")

            # Create auth token
            auth_token = SpotifyAuthorisationToken(access_token=access_token)

            # Search for artists
            results = await self.api_client.search.start(
                query=query, query_type=["artist"], limit=limit, auth_token=auth_token
            )

            artists = results.get("artists", {}).get("items", [])
            logger.debug(f"Found {len(artists)} artists for query: {query}")

            return artists

        except Exception as e:
            logger.error(f"Failed to search artists: {e}")
            return []

    async def close(self):
        """Close the Spotify API client"""
        if self.api_client:
            await self.api_client.close_client()
            logger.debug("Closed Spotify API client")


spotify_search_service = SpotifySearchService()
