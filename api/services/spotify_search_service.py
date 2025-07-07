"""
Spotify search service.
Searches for songs in real-time using the Spotify Web API.
Converts AI-generated search queries into actual song results.
"""

import logging
import spotipy
import random

from typing import List, Optional

from spotipy.oauth2 import SpotifyClientCredentials

from core.singleton import SingletonServiceBase
from core.models import Song, UserContext

from config.settings import settings

from services.data_service import data_loader

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

            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            await self._test_connection()

            logger.info("Spotify Search Service initialized successfully")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Failed to initialize Spotify Search Service: {e}")
            raise RuntimeError(f"Spotify Search Service initialization failed: {e}")

    async def _test_connection(self):
        """Test Spotify API connection"""

        try:
            results = self.spotify.search(q="test", type="track", limit=1)

            if not results or not results.get("tracks"):
                raise Exception("Invalid API response")

        except Exception as e:
            raise Exception(f"Spotify API test failed: {e}")

    async def search_songs_by_mood(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional['UserContext'] = None, count: int = 30, discovery_strategy: str = "balanced") -> List[Song]:
        """
        Search for songs based on mood keywords and preferences.
        
        Args:
            mood_keywords: AI-generated keywords describing the mood
            genres: Preferred genres (optional)
            energy_level: "low", "medium", "high" (optional)
            user_context: User preferences and personality (optional)
            count: Number of songs to return
            discovery_strategy: "new_music", "existing_music", or "balanced"
        Returns:
            List of Song objects
        """

        if not self.spotify:
            raise RuntimeError("Spotify service not properly initialized")

        try:
            all_songs = []

            if discovery_strategy == "existing_music":
                search_queries = self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)

            elif discovery_strategy == "new_music":
                search_queries = self._generate_discovery_queries(mood_keywords, genres, energy_level, user_context)

            else:
                familiar_queries = self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)
                discovery_queries = self._generate_discovery_queries(mood_keywords, genres, energy_level, user_context)
                search_queries = familiar_queries[:len(familiar_queries)//2] + discovery_queries[:len(discovery_queries)//2]

            for query in search_queries:
                songs = await self._search_spotify(query, count // len(search_queries) + 5)
                all_songs.extend(songs)

            unique_songs = self._remove_duplicates(all_songs)
            selected_songs = self._select_best_songs(unique_songs, count, discovery_strategy)

            return selected_songs

        except Exception as e:
            logger.error(f"Spotify search failed: {e}")
            raise RuntimeError(f"Spotify search failed: {e}")

    def _generate_search_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate diverse search queries based on mood and preferences (legacy method)"""

        return self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)

    def _generate_familiar_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate search queries focused on familiar music and user preferences"""

        queries = []

        if user_context and user_context.favorite_artists:
            favorite_artists = user_context.favorite_artists[:8]

            for artist in favorite_artists:
                queries.append(f'artist:"{artist}"')

                if mood_keywords:
                    queries.append(f'{mood_keywords[0]} artist:"{artist}"')

        for keyword in mood_keywords[:2]:
            queries.append(f'{keyword} year:2010-2024')

        if genres:
            genre_artists = data_loader.get_genre_artists()

            for genre in genres[:2]:
                if genre in genre_artists:
                    for artist in genre_artists[genre][:3]:
                        queries.append(f'artist:"{artist}" genre:"{genre}"')

        if user_context and user_context.favorite_genres:
            for genre in user_context.favorite_genres[:3]:
                queries.append(f'genre:"{genre}"')

        return queries[:12]

    def _generate_discovery_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate search queries focused on music discovery and lesser-known tracks"""

        queries = []

        for keyword in mood_keywords[:3]:
            queries.append(f'{keyword} year:1990-2024')
            queries.append(f'{keyword} NOT artist:"Taylor Swift" NOT artist:"Drake" NOT artist:"Ed Sheeran"')

        if genres:
            for genre in genres[:2]:
                queries.append(f'genre:"{genre}" year:2000-2024')

        if energy_level:
            energy_terms = data_loader.get_energy_trigger_words()

            if energy_level in energy_terms:
                for term in energy_terms[energy_level][:2]:
                    queries.append(f'{term}')

        exploration_terms = ["indie", "alternative", "underground", "emerging", "new artist"]

        for term in exploration_terms[:3]:
            if mood_keywords:
                queries.append(f'{mood_keywords[0]} {term}')

        return queries[:10]

    async def _search_spotify(self, query: str, limit: int = 10) -> List[Song]:
        """Perform actual Spotify search"""

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
            raise RuntimeError(f"Spotify search error for '{query}': {e}")

    def _remove_duplicates(self, songs: List[Song]) -> List[Song]:
        """Remove duplicate songs based on title and artist"""

        seen = set()
        unique_songs = []

        for song in songs:
            key = (song.title.lower(), song.artist.lower())

            if key not in seen:
                seen.add(key)
                unique_songs.append(song)

        return unique_songs

    def _select_best_songs(self, songs: List[Song], count: int, discovery_strategy: str = "balanced") -> List[Song]:
        """Select the best songs based on popularity, diversity, and discovery strategy"""

        if len(songs) <= count:
            return songs

        if discovery_strategy == "existing_music":
            sorted_songs = sorted(songs, key=lambda s: s.popularity or 0, reverse=True)
            return sorted_songs[:count]
        
        elif discovery_strategy == "new_music":
            sorted_songs = sorted(songs, key=lambda s: s.popularity or 50)
            low_pop = [s for s in sorted_songs if (s.popularity or 50) < 40]
            med_pop = [s for s in sorted_songs if 40 <= (s.popularity or 50) < 70]
            selected = []
            discovery_count = int(count * 0.6)
            balance_count = count - discovery_count
            selected.extend(low_pop[:discovery_count])
            selected.extend(med_pop[:balance_count])

            if len(selected) < count:
                remaining = [s for s in sorted_songs if s not in selected]
                selected.extend(remaining[:count - len(selected)])

            return selected[:count]

        else:
            sorted_songs = sorted(songs, key=lambda s: s.popularity or 0, reverse=True)
            top_count = int(count * 0.7)
            variety_count = count - top_count
            selected = sorted_songs[:top_count]
            remaining = sorted_songs[top_count:]

            if remaining and variety_count > 0:
                random.shuffle(remaining)
                selected.extend(remaining[:variety_count])

            return selected

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
