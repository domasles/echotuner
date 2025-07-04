import logging
import json

from typing import Optional, List

from services.spotify_search_service import spotify_search_service
from core.models import UserContext, SpotifyArtist
from services.database_service import db_service
from core.singleton import SingletonServiceBase
from services.auth_service import auth_service
from config.settings import settings

logger = logging.getLogger(__name__)

class PersonalityService(SingletonServiceBase):
    """Service for managing user personality and preferences"""

    def _setup_service(self):
        """Initialize the PersonalityService."""

        self.auth_service = auth_service
        self.spotify_search = spotify_search_service

        self._log_initialization("Personality service initialized successfully", logger)

    def __init__(self):
        super().__init__()

    async def initialize(self):
        """Initialize the service"""

        if not hasattr(self.spotify_search, '_initialized') or not self.spotify_search._initialized:
            await self.spotify_search.initialize()

    async def save_user_personality(self, session_id: str, device_id: str, user_context: UserContext) -> bool:
        """Save user personality preferences"""

        try:
            logger.info(f"Starting personality save for session: {session_id}")
            user_info = await self.auth_service.get_user_from_session(session_id)

            if not user_info:
                logger.error("Failed to get user info for personality save")
                return False

            spotify_user_id = user_info.get('spotify_user_id')
            
            # Check if this is a demo account
            if settings.DEMO and spotify_user_id.startswith("demo_user_"):
                logger.info(f"Demo mode: personality not stored server-side for device {device_id}")
                return True
            
            user_id = spotify_user_id
            logger.info(f"Saving personality for user {user_id}")
            success = await db_service.save_user_personality(user_id, spotify_user_id, user_context)

            if success:
                logger.info(f"Successfully saved personality for user {user_id}")

            else:
                logger.error(f"Failed to save personality for user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to save user personality: {e}")
            return False

    async def get_user_personality(self, session_id: str, device_id: str) -> Optional[UserContext]:
        """Get user personality preferences"""

        try:
            user_info = await self.auth_service.get_user_from_session(session_id)

            if not user_info:
                logger.error("Failed to get user info for personality retrieval")
                return None

            spotify_user_id = user_info.get('spotify_user_id')
            
            # Check if this is a demo account
            if settings.DEMO and spotify_user_id.startswith("demo_user_"):
                logger.info(f"Demo mode: personality retrieved from client-side for device {device_id}")
                return None
            
            user_id = spotify_user_id

            user_context_json = await db_service.get_user_personality(user_id)

            if user_context_json:
                user_context_data = json.loads(user_context_json)
                return UserContext(**user_context_data)

        except Exception as e:
            logger.error(f"Failed to get user personality: {e}")

        return None

    async def get_followed_artists(self, session_id: str, device_id: str, limit: int = 50) -> List[SpotifyArtist]:
        """Get user's followed artists from Spotify"""

        try:
            # Check if this is a demo account - if so, return empty list
            user_info = await self.auth_service.get_user_from_session(session_id)
            if not user_info:
                logger.error("Failed to get user info for followed artists")
                return []

            spotify_user_id = user_info.get('spotify_user_id')
            if settings.DEMO and spotify_user_id and spotify_user_id.startswith("demo_user_"):
                logger.info(f"Demo mode: skipping Spotify followed artists for device {device_id}")
                return []

            access_token = await self.auth_service.get_access_token(session_id)

            if not access_token:
                logger.error("No access token available for followed artists")
                return []

            followed_artists = await self.spotify_search.get_followed_artists(access_token, limit)

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

            return artists

        except Exception as e:
            logger.warning(f"Failed to get followed artists (this may be due to insufficient permissions): {e}")
            return []

    async def get_top_artists(self, session_id: str, device_id: str, time_range: str = "medium_term", limit: int = 20) -> List[SpotifyArtist]:
        """Get user's top artists from their listening history"""

        try:
            access_token = await self.auth_service.get_access_token(session_id)

            if not access_token:
                logger.error("No access token available for top artists")
                return []

            top_artists = await self.spotify_search.get_user_top_artists(access_token, time_range, limit)

            artists = []

            for artist_data in top_artists:
                artist = SpotifyArtist(
                    id=artist_data.get('id', ''),
                    name=artist_data.get('name', ''),
                    image_url=artist_data.get('images', [{}])[0].get('url') if artist_data.get('images') else None,
                    genres=artist_data.get('genres', []),
                    popularity=artist_data.get('popularity', 0)
                )

                artists.append(artist)

            logger.info(f"Retrieved {len(artists)} top artists for {time_range}")
            return artists

        except Exception as e:
            logger.warning(f"Failed to get top artists: {e}")
            return []
    
    async def search_artists(self, session_id: str, device_id: str, query: str, limit: int = 20) -> List[SpotifyArtist]:
        """Search for artists on Spotify"""

        try:
            access_token = await self.auth_service.get_access_token(session_id)

            if not access_token:
                logger.error("No access token available for artist search")
                return []

            search_results = await self.spotify_search.search_artists(access_token, query, limit)
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

            return artists

        except Exception as e:
            logger.error(f"Failed to search artists: {e}")
            return []

    async def get_merged_favorite_artists(self, session_id: str, device_id: str, user_context: UserContext) -> List[str]:
        """Get merged list of favorite artists including Spotify data for enhanced AI understanding"""

        try:
            favorite_artists = user_context.favorite_artists or []
            all_artists = set()

            for artist in favorite_artists:
                all_artists.add(artist.lower())

            spotify_artists = []
            followed_artists = await self.get_followed_artists(session_id, device_id, limit=30)
            spotify_artists.extend([artist.name for artist in followed_artists])
            top_artists = await self.get_top_artists(session_id, device_id, "medium_term", limit=20)
            spotify_artists.extend([artist.name for artist in top_artists])
            spotify_added = 0

            for artist in spotify_artists:
                if artist.lower() not in all_artists:
                    favorite_artists.append(artist)
                    all_artists.add(artist.lower())
                    spotify_added += 1

            if spotify_added > 0:
                logger.info(f"Enhanced AI taste understanding: merged {len(followed_artists)} followed + {len(top_artists)} top artists (with overlap removal) = {spotify_added} unique Spotify artists + {len(user_context.favorite_artists or [])} custom artists = {len(favorite_artists)} total")

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

            if user_personality.favorite_genres:
                context_parts.append(f"User's favorite genres: {', '.join(user_personality.favorite_genres)}")

            merged_artists = await self.get_merged_favorite_artists(session_id, device_id, user_personality)
            if merged_artists:
                context_parts.append(f"User's favorite artists: {', '.join(merged_artists)}")

            if user_personality.disliked_artists:
                context_parts.append(f"AVOID these artists (user dislikes): {', '.join(user_personality.disliked_artists)}")

            if user_personality.decade_preference:
                context_parts.append(f"Preferred decades: {', '.join(user_personality.decade_preference)}")

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

personality_service = PersonalityService()
