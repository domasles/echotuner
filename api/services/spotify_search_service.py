import logging
import spotipy
import random

from typing import List, Optional

from spotipy.oauth2 import SpotifyClientCredentials
from services.data_loader import data_loader
from config.settings import settings
from core.models import Song

logger = logging.getLogger(__name__)

class SpotifySearchService:
    """
    Service for searching songs in real-time using Spotify Web API.
    Converts AI-generated search queries into actual song results.
    """
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        
        self.spotify = None
        self.initialized = False
        
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
            
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
            
            await self._test_connection()

            logger.info("Spotify Search Service initialized successfully!")
            self.initialized = True
            
        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Spotify initialization failed: {e}")
            raise RuntimeError(f"Spotify initialization failed: {e}")
        
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        
        return self.initialized
    
    async def _test_connection(self):
        """Test Spotify API connection"""
        try:
            results = self.spotify.search(q="test", type="track", limit=1)

            if not results or not results.get("tracks"):
                raise Exception("Invalid API response")
            
        except Exception as e:
            raise Exception(f"Spotify API test failed: {e}")
    
    async def search_songs_by_mood(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None, count: int = 30) -> List[Song]:
        """
        Search for songs based on mood keywords and preferences.
        
        Args:
            mood_keywords: AI-generated keywords describing the mood
            genres: Preferred genres (optional)
            energy_level: "low", "medium", "high" (optional)
            count: Number of songs to return
              Returns:
            List of Song objects
        """
        
        if not self.initialized:
            await self.initialize()
            
        if not self.spotify:
            raise RuntimeError("Spotify service not properly initialized")
        
        try:
            all_songs = []
            search_queries = self._generate_search_queries(mood_keywords, genres, energy_level)
            
            for query in search_queries:
                songs = await self._search_spotify(query, count // len(search_queries) + 5)
                all_songs.extend(songs)

            unique_songs = self._remove_duplicates(all_songs)
            selected_songs = self._select_best_songs(unique_songs, count)
            
            return selected_songs
            
        except Exception as e:
            logger.error(f"Spotify search failed: {e}")
            raise RuntimeError(f"Spotify search failed: {e}")
    
    def _generate_search_queries(self, mood_keywords: List[str], genres: Optional[List[str]] = None, energy_level: Optional[str] = None) -> List[str]:
        """Generate diverse search queries based on mood and preferences"""
        
        queries = []

        for keyword in mood_keywords[:3]:
            queries.append(keyword)

        if genres:
            genre_artists = data_loader.get_genre_artists()
            
            for genre in genres[:2]:
                queries.append(f"genre:{genre}")

                if mood_keywords:
                    queries.append(f"{mood_keywords[0]} genre:{genre}")

                if genre.lower() in genre_artists:
                    artists = genre_artists[genre.lower()][:3]

                    for artist in artists:
                        queries.append(f'artist:"{artist}"')

                        if mood_keywords:
                            queries.append(f'{mood_keywords[0]} artist:"{artist}"')

        if energy_level:
            energy_terms = data_loader.get_energy_terms()
            
            if energy_level in energy_terms:
                search_terms = energy_terms[energy_level].get("search_terms", [])

                for term in search_terms[:2]:
                    queries.append(term)

        if mood_keywords and energy_level:
            energy_terms = data_loader.get_energy_terms()
            energy_map = {}

            for level, data in energy_terms.items():
                search_terms = data.get("search_terms", [])

                if search_terms:
                    energy_map[level] = search_terms[0]

            if energy_level in energy_map:
                queries.append(f"{mood_keywords[0]} {energy_map[energy_level]}")
        
        return queries[:12]
    
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
    
    def _select_best_songs(self, songs: List[Song], count: int) -> List[Song]:
        """Select the best songs based on popularity and diversity"""

        if len(songs) <= count:
            return songs

        sorted_songs = sorted(songs, key=lambda s: s.popularity or 0, reverse=True)

        top_count = int(count * 0.7)
        variety_count = count - top_count
        
        selected = sorted_songs[:top_count]
        remaining = sorted_songs[top_count:]

        if remaining and variety_count > 0:
            random.shuffle(remaining)
            selected.extend(remaining[:variety_count])
        
        return selected
