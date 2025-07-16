"""
Playlist generator service.
Generates playlists using AI-powered real-time song search.
"""

import logging
import random
import json

from typing import List, Dict, Any, Optional

from core.singleton import SingletonServiceBase
from models import Song, UserContext
from config.settings import settings
from config.app_constants import app_constants

from services.spotify.search import spotify_search_service
from services.data.data import data_loader
from services.ai.ai import ai_service
from services.personality.personality import personality_service

from core.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class PlaylistGeneratorService(SingletonServiceBase):
    """AI service that generates playlists using real-time song search."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the PlaylistGeneratorService."""

        self.spotify_search = spotify_search_service
        self._log_initialization("Playlist generator service initialized successfully", logger)

    async def initialize(self):
        """Initialize the AI model and Spotify search service"""

        try:
            await self.spotify_search.initialize()

            logger.info("AI Playlist Generation initialized successfully!")

        except Exception as e:
            logger.error(f"Playlist generation initialization failed: {e}")
            raise RuntimeError(f"Playlist generation initialization failed: {e}")

    async def generate_playlist(self, prompt: str, user_context: Optional[UserContext] = None, count: int = 30, discovery_strategy: str = "balanced", session_id: str = None, device_id: str = None) -> List[Song]:
        """
        Generate a playlist using AI-powered real-time song search with full personality context.

        Args:
            prompt: User's mood/context description
            user_context: Additional user preferences
            count: Number of songs to generate
            discovery_strategy: "new_music", "existing_music", or "balanced"
            session_id: User session for personality data
            device_id: Device ID for personality data

        Returns:
            List of exactly 'count' songs
        """

        try:
            prompt = UniversalValidator.validate_prompt(prompt)
            count = UniversalValidator.validate_count(count, min_count=1, max_count=100)

            if discovery_strategy not in ["new_music", "existing_music", "balanced"]:
                discovery_strategy = "balanced"

            # Get enhanced personality context if session info provided
            enhanced_prompt = prompt
            if session_id and device_id:
                enhanced_prompt = await personality_service.get_personality_enhanced_context(
                    session_id=session_id, 
                    device_id=device_id, 
                    prompt=prompt
                )

            search_strategy = await self._ai_generate_strategy(enhanced_prompt, user_context, discovery_strategy, original_prompt=prompt)

            songs = await self.spotify_search.search_songs_by_mood(
                mood_keywords=search_strategy["mood_keywords"],
                genres=search_strategy.get("genres"),
                energy_level=search_strategy.get("energy_level"),
                user_context=user_context,
                count=count,
                discovery_strategy=discovery_strategy
            )

            if len(songs) < count:
                additional_songs = await self._get_additional_songs(
                    existing_songs=songs, 
                    target_count=count,
                    search_strategy=search_strategy
                )

                songs.extend(additional_songs)

            if len(songs) < count:
                fallback_songs = await self._get_fallback_songs(
                    existing_songs=songs,
                    target_count=count,
                    search_strategy=search_strategy
                )
                songs.extend(fallback_songs)

            songs = songs[:count]

            if user_context and user_context.disliked_artists:
                disliked_artists_lower = [artist.lower() for artist in user_context.disliked_artists]
                filtered_songs = []

                for song in songs:
                    if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower):
                        filtered_songs.append(song)

                    if len(filtered_songs) < count:
                        additional_needed = count - len(filtered_songs)
                        additional_songs = await self._get_additional_songs(
                            existing_songs=songs, 
                            target_count=additional_needed,
                            search_strategy=search_strategy
                        )

                        for song in additional_songs:
                            if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower):
                                filtered_songs.append(song)

                                if len(filtered_songs) >= count:
                                    break

                        if len(filtered_songs) < count:
                            fallback_songs = await self._get_fallback_songs(
                                existing_songs=filtered_songs,
                                target_count=count,
                                search_strategy=search_strategy
                            )

                            for song in fallback_songs:
                                if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower):
                                    filtered_songs.append(song)

                                    if len(filtered_songs) >= count:
                                        break

                    songs = filtered_songs[:count]

            random.shuffle(songs)

            if len(songs) < count:
                logger.warning(f"Generated only {len(songs)} songs instead of requested {count}. This should not happen.")

            logger.debug(f"Generated {len(songs)} songs using AI + Spotify search (requested: {count})")
            return songs

        except ValueError as e:
            logger.warning(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        except Exception as e:
            logger.error(f"Playlist generation failed: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Playlist generation failed: {sanitized_error}")

    async def _ai_generate_strategy(self, prompt: str, user_context: Optional[UserContext] = None, discovery_strategy: str = "balanced", original_prompt: str = None) -> Dict[str, Any]:
        """Generate search strategy - simplified and user-focused"""

        try:
            # Use original prompt for keyword extraction if available
            prompt_for_keywords = original_prompt or prompt
            
            # Build focused context
            context = f"MODE: {discovery_strategy}\nREQUEST: {prompt_for_keywords}\n"
            
            # Critical: User's preferences
            if user_context:
                if user_context.favorite_artists:
                    context += f"FAVORITE ARTISTS: {', '.join(user_context.favorite_artists[:settings.MAX_FAVORITE_ARTISTS])}\n"
                if user_context.favorite_genres:
                    context += f"FAVORITE GENRES: {', '.join(user_context.favorite_genres[:settings.MAX_FAVORITE_GENRES])}\n"
                if user_context.decade_preference:
                    context += f"PREFERRED DECADES: {', '.join(user_context.decade_preference[:settings.MAX_PREFERRED_DECADES])}\n"
                if user_context.disliked_artists:
                    context += f"NEVER USE: {', '.join(user_context.disliked_artists[:settings.MAX_DISLIKED_ARTISTS])}\n"

            # Enhanced AI prompt - focus on user's preferences AND decades
            if discovery_strategy == "existing_music":
                instruction = "ONLY use the favorite artists, genres, and decades listed above. Do not suggest any other artists or time periods."
            elif discovery_strategy == "new_music":
                instruction = "Find NEW artists similar to favorites from the user's preferred decades. Avoid mainstream hits."
            else:
                instruction = "Mix user's favorites with some new discoveries from their preferred decades."

            # Special handling for nostalgic requests
            if "nostalgic" in prompt_for_keywords.lower() or "nostalgia" in prompt_for_keywords.lower():
                instruction += " Focus on music from the user's preferred decades that evokes nostalgia and memories."

            # Use full personality context if available, otherwise use basic context
            ai_prompt = f"""
{prompt if original_prompt else context}

{instruction}

IMPORTANT: Extract mood keywords ONLY from this request: "{prompt_for_keywords}"
If user mentions "nostalgic" or "nostalgia", extract keywords that relate to their preferred decades, not current music.

Extract mood keywords from the request and return JSON:
{{"mood_keywords": ["word1", "word2", "word3"], "genres": ["genre1", "genre2"], "energy_level": "medium"}}
"""

            response_text = await self._call_ai_model(ai_prompt)
            
            # Parse JSON response
            try:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    strategy = json.loads(response_text[start_idx:end_idx])
                    if "mood_keywords" in strategy:
                        return strategy
            except json.JSONDecodeError:
                pass

            # Fallback parsing
            return self._parse_ai_response(response_text, prompt_for_keywords, user_context)

        except Exception as e:
            logger.error(f"AI strategy generation failed: {e}")
            raise RuntimeError(f"AI strategy generation failed: {e}")

    async def _parse_ai_response(self, response_text: str, prompt: str, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """Simple fallback parsing"""
        
        # Extract basic info from original prompt only
        words = prompt.lower().split()
        mood_keywords = [word for word in words if len(word) > 2][:settings.MAX_SONGS_PER_PLAYLIST//10]
        
        # Default genre based on user preferences or fallback
        genres = ["pop", "rock"]
        if user_context and user_context.favorite_genres:
            genres = user_context.favorite_genres[:settings.MAX_FAVORITE_GENRES//5]
        
        return {
            "mood_keywords": mood_keywords or ["music", "songs", "playlist"],
            "genres": genres,
            "energy_level": "medium"
        }

    async def _get_additional_songs(self, existing_songs: List[Song], target_count: int, search_strategy: Dict[str, Any]) -> List[Song]:
        """Get additional songs to reach target count"""

        needed = target_count - len(existing_songs)

        if needed <= 0:
            return []

        additional_songs = []
        broader_keywords = data_loader.get_broader_keywords()

        for keyword in broader_keywords:
            if len(additional_songs) >= needed:
                break

            songs = await self.spotify_search.search_songs_by_mood(
                mood_keywords=[keyword],
                genres=search_strategy.get("genres"),
                energy_level=search_strategy.get("energy_level"),
                count=needed
            )

            new_songs = [s for s in songs if s not in existing_songs and s not in additional_songs]
            additional_songs.extend(new_songs[:needed - len(additional_songs)])

        return additional_songs

    async def _get_fallback_songs(self, existing_songs: List[Song], target_count: int, search_strategy: Dict[str, Any]) -> List[Song]:
        """Get fallback songs using broader search criteria when targeted search fails"""

        needed = target_count - len(existing_songs)

        if needed <= 0:
            return []

        fallback_songs = []
        broader_genres = ["pop", "rock", "hip-hop", "electronic", "indie", "alternative"]

        for genre in broader_genres:
            if len(fallback_songs) >= needed:
                break

            try:
                songs = await self.spotify_search.search_songs_by_mood(
                    mood_keywords=["popular", "trending"],
                    genres=[genre],
                    energy_level="medium",
                    count=needed
                )

                new_songs = [s for s in songs if s not in existing_songs and s not in fallback_songs]
                fallback_songs.extend(new_songs[:needed - len(fallback_songs)])

            except Exception as e:
                logger.warning(f"Fallback search for genre {genre} failed: {e}")
                continue

        if len(fallback_songs) < needed:
            try:
                generic_songs = await self.spotify_search.search_songs_by_mood(
                    mood_keywords=["music", "song"],
                    genres=None,
                    energy_level=None,
                    count=needed
                )

                new_songs = [s for s in generic_songs if s not in existing_songs and s not in fallback_songs]
                fallback_songs.extend(new_songs[:needed - len(fallback_songs)])

            except Exception as e:
                logger.warning(f"Generic fallback search failed: {e}")

        logger.debug(f"Fallback search provided {len(fallback_songs)} additional songs")
        return fallback_songs

    async def _call_ai_model(self, prompt: str) -> str:
        """Universal method to call different AI models"""

        try:
            return await ai_service.generate_text(prompt, model_id=None)

        except Exception as e:
            logger.error(f"AI model call failed: {e}")
            raise RuntimeError(f"AI model call failed: {e}")

playlist_generator_service = PlaylistGeneratorService()
