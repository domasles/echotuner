"""
Spotify search service.
Searches for songs in real-time using the Spotify Web API.
Fast song verification and metadata retrieval for AI-generated suggestions.
"""

import logging
import spotipy

from typing import List, Optional

from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyClientCredentials

from application.core.singleton import SingletonServiceBase
from application import Song, UserContext
from infrastructure.config.settings import settings

from infrastructure.config.app_constants import app_constants

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class SpotifySearchService(SingletonServiceBase):
    """Service for searching songs in real-time using Spotify Web API."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the SpotifySearchService."""

        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.spotify = None

        self._log_initialization("Spotify search service initialized successfully", logger)

    async def initialize(self):
        """Initialize Spotify client"""
            
        try:
            if not self.client_id or not self.client_secret:
                logger.error("Spotify credentials not found")
                raise RuntimeError("Spotify credentials are required. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

            cache_handler = CacheFileHandler(cache_path=app_constants.SPOTIFY_CACHE_PATH)

            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
                cache_handler=cache_handler
            )

            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            await self._test_connection()

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Failed to initialize Spotify Search Service: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Spotify Search Service initialization failed: {sanitized_error}")

    async def _test_connection(self):
        """Test Spotify API connection"""

        try:
            results = self.spotify.search(q="test", type="track", limit=1)

            if not results or not results.get("tracks"):
                raise Exception("Invalid API response")

        except Exception as e:
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))
            raise Exception(f"Spotify API test failed: {sanitized_error}")

    async def _search_spotify(self, query: str, limit: int = None) -> List[Song]:
        """Perform actual Spotify search"""

        if limit is None:
            limit = settings.MAX_SONGS_PER_PLAYLIST // 3

        try:
            results = self.spotify.search(q=query, type="track", limit=limit)
            songs = []

            for track in results["tracks"]["items"]:
                song = Song(
                    title=track["name"],
                    artist=", ".join([artist["name"] for artist in track["artists"]]),
                    album=track["album"]["name"],
                    spotify_id=track["id"],
                    duration_ms=track.get("duration_ms"),
                    popularity=track.get("popularity", 50)
                )

                songs.append(song)

            return songs

        except Exception as e:
            logger.error(f"Spotify search error for '{query}': {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Spotify search error for '{query}': {sanitized_error}")

    async def get_followed_artists(self, access_token: str, limit: int = 50) -> List[dict]:
        """Get user's followed artists using access token"""
    
        try:
            spotify_user = spotipy.Spotify(auth=access_token)
            results = spotify_user.current_user_followed_artists(limit=limit)
            artists = results.get('artists', {}).get('items', [])
            logger.debug(f"Retrieved {len(artists)} followed artists")

            return artists

        except Exception as e:
            logger.error(f"Failed to get followed artists: {e}")
            return []

    async def get_user_top_artists(self, access_token: str, time_range: str = "medium_term", limit: int = 20) -> List[dict]:
        """Get user's top artists from listening history using access_token"""

        try:
            spotify_user = spotipy.Spotify(auth=access_token)
            results = spotify_user.current_user_top_artists(time_range=time_range, limit=limit)
            artists = results.get('items', [])
            logger.debug(f"Retrieved {len(artists)} top artists for time range: {time_range}")

            return artists
            
        except Exception as e:
            logger.error(f"Failed to get top artists: {e}")
            return []

    async def search_artists(self, access_token: str, query: str, limit: int = 20) -> List[dict]:
        """Search for artists using access token"""

        try:
            spotify_user = spotipy.Spotify(auth=access_token)
            results = spotify_user.search(q=query, type='artist', limit=limit)
            artists = results.get('artists', {}).get('items', [])
            logger.debug(f"Found {len(artists)} artists for query: {query}")

            return artists

        except Exception as e:
            logger.error(f"Failed to search artists: {e}")
            return []

spotify_search_service = SpotifySearchService()
