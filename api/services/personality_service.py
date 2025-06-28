import json
import logging
import sqlite3
from typing import Optional, List, Dict, Any
from core.models import UserContext, SpotifyArtist
from services.auth_service import AuthService
from services.spotify_search_service import SpotifySearchService
from config.app_constants import AppConstants
from config.settings import settings

logger = logging.getLogger(__name__)

class PersonalityService:
    """Service for managing user personality and preferences"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.spotify_search = SpotifySearchService()
        
    async def initialize(self):
        """Initialize the service"""
        await self.spotify_search.initialize()
        self._create_tables()
        
    def _create_tables(self):
        """Create personality tables if they don't exist"""
        try:
            with sqlite3.connect(AppConstants.DATABASE_FILENAME) as conn:
                cursor = conn.cursor()
                
                # Create user_personalities table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_personalities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        spotify_user_id TEXT,
                        user_context TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id)
                    )
                ''')
                
                # Create trigger to update updated_at
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_user_personalities_timestamp 
                    AFTER UPDATE ON user_personalities
                    BEGIN
                        UPDATE user_personalities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                ''')
                
                conn.commit()
                logger.info("Personality tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create personality tables: {e}")
            raise
    
    async def save_user_personality(self, session_id: str, device_id: str, user_context: UserContext) -> bool:
        """Save user personality preferences"""
        try:
            # Get user info from session
            user_info = await self.auth_service.get_user_from_session(session_id)
            if not user_info:
                logger.error("Failed to get user info for personality save")
                return False
                
            spotify_user_id = user_info.get('spotify_user_id')
            # Use spotify_user_id directly for cross-device personality sync
            user_id = spotify_user_id
            
            # Serialize user context
            user_context_json = user_context.model_dump_json()

            with sqlite3.connect(AppConstants.DATABASE_FILENAME) as conn:
                cursor = conn.cursor()
                
                # Insert or update personality
                cursor.execute('''
                    INSERT OR REPLACE INTO user_personalities 
                    (user_id, spotify_user_id, user_context, created_at, updated_at)
                    VALUES (?, ?, ?, 
                        COALESCE((SELECT created_at FROM user_personalities WHERE user_id = ?), CURRENT_TIMESTAMP),
                        CURRENT_TIMESTAMP)
                ''', (user_id, spotify_user_id, user_context_json, user_id))
                
                conn.commit()
                logger.info(f"Saved personality for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save user personality: {e}")
            return False
    
    async def get_user_personality(self, session_id: str, device_id: str) -> Optional[UserContext]:
        """Get user personality preferences"""
        try:
            # Get user info from session
            user_info = await self.auth_service.get_user_from_session(session_id)
            if not user_info:
                logger.error("Failed to get user info for personality retrieval")
                return None
                
            spotify_user_id = user_info.get('spotify_user_id')
            # Use spotify_user_id directly for cross-device personality sync
            user_id = spotify_user_id

            with sqlite3.connect(AppConstants.DATABASE_FILENAME) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_context FROM user_personalities 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if result:
                    user_context_data = json.loads(result[0])
                    return UserContext(**user_context_data)
                    
        except Exception as e:
            logger.error(f"Failed to get user personality: {e}")
            
        return None
    
    async def get_followed_artists(self, session_id: str, device_id: str, limit: int = 50) -> List[SpotifyArtist]:
        """Get user's followed artists from Spotify"""
        try:
            # Get access token
            access_token = await self.auth_service.get_access_token(session_id)
            if not access_token:
                logger.error("No access token available for followed artists")
                return []
            
            # Use Spotify search service to get followed artists
            followed_artists = await self.spotify_search.get_followed_artists(access_token, limit)
            
            # Convert to SpotifyArtist objects
            artists = []
            for artist_data in followed_artists:
                artist = SpotifyArtist(
                    id=artist_data.get('id', ''),
                    name=artist_data.get('name', ''),
                    image_url=artist_data.get('images', [{}])[0].get('url') if artist_data.get('images') else None,
                    genres=artist_data.get('genres', []),
                    popularity=artist_data.get('popularity', 0)
                )
                artists.append(artist)
            
            logger.info(f"Retrieved {len(artists)} followed artists")
            return artists
            
        except Exception as e:
            logger.warning(f"Failed to get followed artists (this may be due to insufficient permissions): {e}")
            # Return empty list if we can't access followed artists
            # This is not a critical error - user can still add artists manually
            return []
    
    async def search_artists(self, session_id: str, device_id: str, query: str, limit: int = 20) -> List[SpotifyArtist]:
        """Search for artists on Spotify"""
        try:
            # Get access token
            access_token = await self.auth_service.get_access_token(session_id)
            if not access_token:
                logger.error("No access token available for artist search")
                return []
            
            # Search artists using Spotify
            search_results = await self.spotify_search.search_artists(access_token, query, limit)
            
            # Convert to SpotifyArtist objects
            artists = []
            for artist_data in search_results:
                artist = SpotifyArtist(
                    id=artist_data.get('id', ''),
                    name=artist_data.get('name', ''),
                    image_url=artist_data.get('images', [{}])[0].get('url') if artist_data.get('images') else None,
                    genres=artist_data.get('genres', []),
                    popularity=artist_data.get('popularity', 0)
                )
                artists.append(artist)
            
            logger.info(f"Found {len(artists)} artists for query: {query}")
            return artists
            
        except Exception as e:
            logger.error(f"Failed to search artists: {e}")
            return []
    
    async def get_merged_favorite_artists(self, session_id: str, device_id: str, user_context: UserContext) -> List[str]:
        """Get merged list of favorite artists including Spotify followed artists if enabled"""
        try:
            favorite_artists = user_context.favorite_artists or []
            
            # If include_spotify_artists is enabled, add followed artists
            if user_context.include_spotify_artists:
                followed_artists = await self.get_followed_artists(session_id, device_id)
                followed_artist_names = [artist.name for artist in followed_artists]
                
                # Merge and deduplicate artist names (case-insensitive)
                all_artists = set()
                for artist in favorite_artists:
                    all_artists.add(artist.lower())
                
                for artist in followed_artist_names:
                    if artist.lower() not in all_artists:
                        favorite_artists.append(artist)
                        all_artists.add(artist.lower())
                
                logger.info(f"Merged {len(followed_artist_names)} Spotify artists with {len(user_context.favorite_artists or [])} custom artists")
            
            return favorite_artists
            
        except Exception as e:
            logger.error(f"Failed to merge favorite artists: {e}")
            return user_context.favorite_artists or []

    async def get_personality_enhanced_context(self, session_id: str, device_id: str, prompt: str) -> str:
        """Get enhanced context for AI including personality preferences"""
        try:
            user_personality = await self.get_user_personality(session_id, device_id)
            if not user_personality:
                return f"User prompt: {prompt}"
            
            context_parts = [f"User prompt: {prompt}"]
            
            # Add personality context
            if user_personality.favorite_genres:
                context_parts.append(f"User's favorite genres: {', '.join(user_personality.favorite_genres)}")
            
            # Get merged favorite artists (including Spotify if enabled)
            merged_artists = await self.get_merged_favorite_artists(session_id, device_id, user_personality)
            if merged_artists:
                context_parts.append(f"User's favorite artists: {', '.join(merged_artists)}")
            
            if user_personality.disliked_artists:
                context_parts.append(f"AVOID these artists (user dislikes): {', '.join(user_personality.disliked_artists)}")
            
            if user_personality.decade_preference:
                context_parts.append(f"Preferred decades: {', '.join(user_personality.decade_preference)}")
            
            # Add mood-based preferences
            mood_preferences = []
            if user_personality.happy_music_preference:
                mood_preferences.append(f"When happy: {user_personality.happy_music_preference}")
            if user_personality.sad_music_preference:
                mood_preferences.append(f"When sad: {user_personality.sad_music_preference}")
            if user_personality.workout_music_preference:
                mood_preferences.append(f"For workouts: {user_personality.workout_music_preference}")
            if user_personality.focus_music_preference:
                mood_preferences.append(f"For focus: {user_personality.focus_music_preference}")
            if user_personality.relaxation_music_preference:
                mood_preferences.append(f"For relaxation: {user_personality.relaxation_music_preference}")
            if user_personality.party_music_preference:
                mood_preferences.append(f"For parties: {user_personality.party_music_preference}")
            
            if mood_preferences:
                context_parts.append(f"User's mood preferences: {'; '.join(mood_preferences)}")
            
            # Add other preferences
            if user_personality.discovery_openness:
                context_parts.append(f"Discovery openness: {user_personality.discovery_openness}")
            
            if user_personality.explicit_content_preference:
                context_parts.append(f"Explicit content preference: {user_personality.explicit_content_preference}")
            
            if user_personality.instrumental_preference:
                context_parts.append(f"Instrumental music preference: {user_personality.instrumental_preference}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to get personality enhanced context: {e}")
            return f"User prompt: {prompt}"
