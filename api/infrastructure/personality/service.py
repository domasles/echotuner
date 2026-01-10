"""
Peonality service.
Manages user personality and preferences, including saving and retrieving user context, fetching followed artists, and enhancing AI context with personality data.
"""

import logging
import json

from datetime import datetime
from typing import Optional, List

from application import UserContext, SpotifyArtist
from infrastructure.singleton import SingletonServiceBase

from domain.config.settings import settings

from infrastructure.spotify.search_service import spotify_search_service
from infrastructure.database.repository import repository
from infrastructure.database.models.users import UserPersonality
from infrastructure.auth.service import oauth_service

logger = logging.getLogger(__name__)


class PersonalityService(SingletonServiceBase):
    """Service for managing user personality and preferences"""

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the PersonalityService."""

        self.oauth_service = oauth_service
        self.spotify_search = spotify_search_service
        self.repository = repository

    async def save_user_personality_by_user_id(self, user_id: str, user_context: UserContext) -> bool:
        """Save user personality preferences by user_id (unified auth system)."""
        try:
            logger.debug(f"Saving personality for user {user_id}")

            # Validate JSON context for security
            from domain.shared.validation.validators import UniversalValidator

            validated_context = UniversalValidator.validate_json_context(user_context.context)

            # Check if user personality already exists
            existing_personality = await self.repository.get_by_field(UserPersonality, "user_id", user_id)

            personality_data = {
                "user_id": user_id,
                "user_context": json.dumps(validated_context),
                "updated_at": datetime.now(),
            }

            if existing_personality:
                success = await self.repository.update(UserPersonality, existing_personality.id, personality_data)
            else:
                personality_data["created_at"] = datetime.now()
                result = await self.repository.create(UserPersonality, personality_data)
                success = result is not None

            if success:
                logger.debug(f"Successfully saved personality for user {user_id}")
            else:
                logger.error(f"Failed to save personality for user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to save user personality for user {user_id}: {e}")
            return False

    async def get_user_personality_by_user_id(self, user_id: str) -> Optional[UserContext]:
        """Get user personality by user_id (unified auth system)."""
        try:
            user_personality = await self.repository.get_by_field(UserPersonality, "user_id", user_id)

            if user_personality:
                user_context_data = json.loads(user_personality.user_context)
                return UserContext(context=user_context_data)
            else:
                logger.debug(f"No personality data found for user {user_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to get user personality for user {user_id}: {e}")
            return None

    async def get_followed_artists_by_user_id(self, user_id: str, limit: int = 50) -> List[SpotifyArtist]:
        """Get user's followed artists by user_id (unified auth system)."""
        try:
            # In shared mode, don't pull followed artists from Spotify
            if settings.SHARED:
                logger.debug("Shared mode enabled - not pulling followed artists from Spotify")
                return []

            access_token = await self.oauth_service.get_access_token_by_user_id(user_id)

            if not access_token:
                logger.error(f"No access token available for followed artists for user {user_id}")
                return []

            followed_artists = await self.spotify_search.get_followed_artists(access_token, limit)
            artists = []

            for artist_data in followed_artists:
                artist = SpotifyArtist(
                    id=artist_data.get("id", ""),
                    name=artist_data.get("name", ""),
                    image_url=artist_data.get("images", [{}])[0].get("url") if artist_data.get("images") else None,
                    genres=artist_data.get("genres", []),
                    popularity=artist_data.get("popularity", 0),
                )
                artists.append(artist)

            return artists

        except Exception as e:
            logger.warning(
                f"Failed to get followed artists for user {user_id} (this may be due to insufficient permissions): {e}"
            )
            return []

    async def search_artists_by_user_id(self, user_id: str, query: str, limit: int = 20) -> List[SpotifyArtist]:
        """Search for artists on Spotify by user_id (unified auth system)."""

        try:
            access_token = await self.oauth_service.get_access_token_by_user_id(user_id)

            if not access_token:
                logger.error(f"No access token available for artist search for user {user_id}")
                return []

            search_results = await self.spotify_search.search_artists(access_token, query, limit)
            artists = []

            for artist_data in search_results:
                artist = SpotifyArtist(
                    id=artist_data.get("id", ""),
                    name=artist_data.get("name", ""),
                    image_url=artist_data.get("images", [{}])[0].get("url") if artist_data.get("images") else None,
                    genres=artist_data.get("genres", []),
                    popularity=artist_data.get("popularity", 0),
                )

                artists.append(artist)

            return artists

        except Exception as e:
            logger.error(f"Failed to search artists for user {user_id}: {e}")
            return []

    async def get_merged_favorite_artists_by_user_id(self, user_id: str, user_context: UserContext) -> List[str]:
        """Get merged list of favorite artists including Spotify data for enhanced AI understanding (unified auth system)"""
        try:
            # Get favorite artists from flexible JSON context
            favorite_artists = []
            if user_context.context.get("favorite_artists"):
                fav_artists = user_context.context["favorite_artists"]
                if isinstance(fav_artists, list):
                    favorite_artists = fav_artists

            all_artists = set()

            for artist in favorite_artists:
                all_artists.add(artist.lower())

            # In shared mode, don't pull followed artists from Spotify
            if not settings.SHARED:
                try:
                    followed_artists = await self.get_followed_artists_by_user_id(user_id, limit=50)
                    for artist in followed_artists:
                        all_artists.add(artist.name.lower())
                except Exception as e:
                    logger.warning(f"Could not fetch followed artists for user {user_id}: {e}")

            return list(all_artists)

        except Exception as e:
            logger.error(f"Failed to merge favorite artists for user {user_id}: {e}")
            # Fallback to context data if available
            if user_context.context.get("favorite_artists"):
                fav_artists = user_context.context["favorite_artists"]
                if isinstance(fav_artists, list):
                    return fav_artists
            return []


personality_service = PersonalityService()
