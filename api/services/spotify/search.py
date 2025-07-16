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
from models import Song, UserContext
from config.settings import settings
from config.app_constants import app_constants

from services.data.data import data_loader

from utils.input_validator import UniversalValidator

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

    async def search_songs_by_mood(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None, count: int = 30, discovery_strategy: str = "balanced") -> List[Song]:
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
                # Only use balanced if NO user context provided at all
                if not user_context:
                    # No user context, use balanced approach
                    familiar = self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)
                    discovery = self._generate_discovery_queries(mood_keywords, genres, energy_level, user_context)
                    search_queries = familiar[:settings.MAX_SONGS_PER_PLAYLIST//6] + discovery[:settings.MAX_SONGS_PER_PLAYLIST//6]
                else:
                    # User has context, default to existing music
                    search_queries = self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)

            # Search and collect results
            for query in search_queries:
                songs = await self._search_spotify(query, settings.MAX_SONGS_PER_PLAYLIST // 3)
                all_songs.extend(songs)

            unique_songs = self._remove_duplicates(all_songs)
            selected_songs = self._select_best_songs(unique_songs, count, discovery_strategy)

            return selected_songs

        except Exception as e:
            logger.error(f"Spotify search failed: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Spotify search failed: {sanitized_error}")

    def _generate_search_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate diverse search queries based on mood and preferences (legacy method)"""

        return self._generate_familiar_queries(mood_keywords, genres, energy_level, user_context)

    def _generate_familiar_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate queries ONLY from user's favorite artists and decades"""

        queries = []
        
        # Build year ranges from user's decade preferences
        year_ranges = self._get_user_year_ranges(user_context)
        
        # STRICT: Only user's favorite artists - nothing else
        if user_context and user_context.favorite_artists:
            for artist in user_context.favorite_artists[:settings.MAX_FAVORITE_ARTISTS]:
                queries.append(f'artist:"{artist}"')
                # Add mood + artist combination
                for keyword in mood_keywords[:settings.MAX_SONGS_PER_PLAYLIST//15]:
                    queries.append(f'artist:"{artist}" {keyword}')
        
        # Use user's favorite genres with their preferred decades
        if user_context and user_context.favorite_genres:
            for genre in user_context.favorite_genres[:settings.MAX_FAVORITE_GENRES]:
                for year_range in year_ranges[:settings.MAX_PREFERRED_DECADES]:
                    queries.append(f'genre:"{genre}" {year_range}')
        
        # Use mood with user's preferred decades
        if user_context and user_context.decade_preference:
            for keyword in mood_keywords[:settings.MAX_SONGS_PER_PLAYLIST//15]:
                for year_range in year_ranges[:settings.MAX_PREFERRED_DECADES]:
                    queries.append(f'{keyword} {year_range}')
        
        # Last resort: use mood with broad year range
        if not queries:
            default_year_range = f"year:{app_constants.POPULAR_YEARS[0]}-{app_constants.POPULAR_YEARS[-1]}"
            for keyword in mood_keywords[:settings.MAX_SONGS_PER_PLAYLIST//15]:
                queries.append(f'{keyword} {default_year_range}')

        return queries

    def _generate_discovery_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, user_context: Optional[UserContext] = None) -> List[str]:
        """Generate discovery queries respecting user's decade preferences"""

        queries = []
        
        # Get mainstream artists from data to exclude
        genre_artists = data_loader.get_genre_artists()
        mainstream_artists = []
        for genre in ["pop", "mainstream", "top 40"]:
            if genre in genre_artists:
                mainstream_artists.extend(genre_artists[genre][:settings.MAX_DISLIKED_ARTISTS])
        
        # Build exclusions from user's dislikes or mainstream artists
        exclusions = []
        if user_context and user_context.disliked_artists:
            exclusions = [f'NOT artist:"{artist}"' for artist in user_context.disliked_artists[:settings.MAX_DISLIKED_ARTISTS]]
        else:
            exclusions = [f'NOT artist:"{artist}"' for artist in mainstream_artists[:settings.MAX_DISLIKED_ARTISTS]]

        # Use user's preferred decades for discovery
        year_ranges = self._get_user_year_ranges(user_context)
        
        # Discovery with mood and user's preferred decades
        exclusion_str = " ".join(exclusions)
        for keyword in mood_keywords[:settings.MAX_SONGS_PER_PLAYLIST//15]:
            for year_range in year_ranges[:settings.MAX_PREFERRED_DECADES]:
                base_query = f'{keyword} indie {year_range}'
                
                # Add exclusions but respect 250-character Spotify limit
                full_query = f'{base_query} {exclusion_str}'
                if len(full_query) > 250:
                    # Truncate exclusions to fit within 250 characters
                    available_space = 250 - len(base_query) - 1  # -1 for space
                    truncated_exclusions = []
                    current_length = 0
                    
                    for exclusion in exclusions:
                        if current_length + len(exclusion) + 1 <= available_space:  # +1 for space
                            truncated_exclusions.append(exclusion)
                            current_length += len(exclusion) + 1
                        else:
                            break
                    
                    final_query = f'{base_query} {" ".join(truncated_exclusions)}' if truncated_exclusions else base_query
                else:
                    final_query = full_query
                
                queries.append(final_query)

        # Discovery with genres and user's preferred decades
        if genres:
            for genre in genres[:settings.MAX_FAVORITE_GENRES]:
                for year_range in year_ranges[:settings.MAX_PREFERRED_DECADES]:
                    queries.append(f'genre:"{genre}" underground {year_range}')

        return queries

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
        """Simple song selection based on discovery strategy"""

        if len(songs) <= count:
            return songs

        if discovery_strategy == "existing_music":
            # STRICT: Only high popularity songs (60+) - NO random artists
            high_pop_songs = [s for s in songs if (s.popularity or 0) >= 60]
            if len(high_pop_songs) >= count:
                return high_pop_songs[:count]
            
            # If not enough high popularity, fill with medium (50+)
            med_pop_songs = [s for s in songs if 50 <= (s.popularity or 0) < 60]
            selected = high_pop_songs + med_pop_songs
            return selected[:count]
        
        elif discovery_strategy == "new_music":
            # Low popularity for discovery
            return sorted(songs, key=lambda s: s.popularity or 50)[:count]
        
        else:
            # Balanced mix
            sorted_songs = sorted(songs, key=lambda s: s.popularity or 0, reverse=True)
            popular = sorted_songs[:count//2]
            discovery = sorted_songs[count//2:]
            return popular + discovery[:count - len(popular)]

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

    def _get_user_year_ranges(self, user_context: Optional[UserContext] = None) -> List[str]:
        """Get user's year ranges directly from decade preferences"""
        
        year_ranges = []
        
        if user_context and user_context.decade_preference:
            # User context now contains year ranges like "1950-1959"
            for year_range in user_context.decade_preference:
                year_ranges.append(f"year:{year_range}")
        
        # Fallback to popular years if no preferences
        if not year_ranges:
            year_ranges = [f"year:{app_constants.POPULAR_YEARS[0]}-{app_constants.POPULAR_YEARS[-1]}"]
        
        return year_ranges

spotify_search_service = SpotifySearchService()
