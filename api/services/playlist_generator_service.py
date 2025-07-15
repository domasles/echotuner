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

from services.spotify_search_service import spotify_search_service
from services.data_service import data_loader
from services.ai_service import ai_service

from utils.input_validator import InputValidator

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

    async def generate_playlist(self, prompt: str, user_context: Optional[UserContext] = None, count: int = 30, discovery_strategy: str = "balanced") -> List[Song]:
        """
        Generate a playlist using AI-powered real-time song search.

        Args:
            prompt: User's mood/context description
            user_context: Additional user preferences
            count: Number of songs to generate
            discovery_strategy: "new_music", "existing_music", or "balanced"

        Returns:
            List of exactly 'count' songs
        """

        try:
            prompt = InputValidator.validate_prompt(prompt)
            count = InputValidator.validate_count(count, min_count=1, max_count=100)

            if discovery_strategy not in ["new_music", "existing_music", "balanced"]:
                discovery_strategy = "balanced"

            search_strategy = await self._ai_generate_strategy(prompt, user_context, discovery_strategy)

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
            sanitized_error = InputValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Playlist generation failed: {sanitized_error}")

    async def _ai_generate_strategy(self, prompt: str, user_context: Optional[UserContext] = None, discovery_strategy: str = "balanced") -> Dict[str, Any]:
        """Generate search strategy using AI model"""

        try:
            context = f"User prompt: {prompt}\n\n"
            context += "CRITICAL CONSTRAINTS:\n"

            if user_context:
                if user_context.disliked_artists:
                    context += f"STRICTLY FORBIDDEN artists that must be avoided at ALL COSTS: {', '.join(user_context.disliked_artists)}\n\n"

                context += "USER PREFERENCES:\n"

                if user_context.favorite_genres:
                    context += f"Preferred genres (prioritize these): {', '.join(user_context.favorite_genres)}\n"

                if user_context.favorite_artists:
                    context += f"Favorite artists (include similar artists): {', '.join(user_context.favorite_artists)}\n"

                if user_context.energy_preference:
                    context += f"Energy preference: {user_context.energy_preference}\n"

                if user_context.decade_preference:
                    context += f"Preferred decades: {', '.join(user_context.decade_preference)}\n"

            context += f"\nDISCOVERY STRATEGY: {discovery_strategy}\n"

            if discovery_strategy == "new_music":
                context += "PRIORITIZE discovering new artists and hidden gems. Focus on lesser-known tracks and emerging artists.\n"

            elif discovery_strategy == "existing_music":
                context += "PRIORITIZE familiar favorites from user's taste profile. Focus on artists and songs similar to user's preferences.\n"

            else:
                context += "BALANCE between familiar favorites and new discoveries. Mix popular tracks with some hidden gems.\n"

            if user_context:
                mood_preferences = []

                if user_context.happy_music_preference:
                    mood_preferences.append(f"When happy: {user_context.happy_music_preference}")

                if user_context.sad_music_preference:
                    mood_preferences.append(f"When sad: {user_context.sad_music_preference}")

                if user_context.workout_music_preference:
                    mood_preferences.append(f"For workouts: {user_context.workout_music_preference}")

                if user_context.focus_music_preference:
                    mood_preferences.append(f"For focus: {user_context.focus_music_preference}")

                if user_context.relaxation_music_preference:
                    mood_preferences.append(f"For relaxation: {user_context.relaxation_music_preference}")

                if user_context.party_music_preference:
                    mood_preferences.append(f"For parties: {user_context.party_music_preference}")

                if mood_preferences:
                    context += f"Mood preferences: {'; '.join(mood_preferences)}\n"

                if user_context.discovery_openness:
                    context += f"Discovery openness: {user_context.discovery_openness}\n"

                if user_context.explicit_content_preference:
                    context += f"Explicit content preference: {user_context.explicit_content_preference}\n"

                if user_context.instrumental_preference:
                    context += f"Instrumental music preference: {user_context.instrumental_preference}\n"

            genre_patterns = data_loader.get_genre_patterns()
            genre_artists = data_loader.get_genre_artists()

            activity_patterns = data_loader.get_activity_patterns()
            activity_energy_mapping = data_loader.get_activity_energy_mapping()

            mood_patterns = data_loader.get_mood_patterns()

            available_genres = list(genre_patterns.keys())
            available_activities = list(activity_patterns.keys())
            activity_energies = {k: v for k, v in activity_energy_mapping.items() if k in available_activities}
            available_moods = list(mood_patterns.keys())

            genre_examples = {}

            for genre in available_genres:
                if genre in genre_artists:
                    artists = genre_artists[genre][:3]
                    genre_examples[genre] = f"{genre} (e.g., {', '.join(artists)})"

                else:
                    genre_examples[genre] = genre

            ai_prompt = f"""
                You are an expert Spotify music curator AI. Analyze user input ({context}) with access to:
                - Genres, example artists: {', '.join(genre_examples.values())}
                - Activities, their energy levels: {activity_energies}
                - Moods: {', '.join(available_moods)}

                Follow strict rules:

                1. Match genres precisely using artist examples.
                - Hip hop/rap → only hip hop, trap, rap genres
                - Pop → pop, dance pop, mainstream only
                - Rock → rock, alternative, metal only
                - Never mix incompatible genres.

                2. Treat any mentioned artist as valid; identify their genre. Respect user's favorite and avoided artists.
                3. Consider user personality: mood, preferences, discovery openness, decades, explicit/instrumental, and context.
                4. Match energy level ("low", "medium", "high") based on activity and mood.

                Return JSON with:
                - mood_keywords (3-5)
                - genres (2-3 from list)
                - energy_level
                - brief explanation considering user preferences.

                Examples:
                - "I want rap music" → genres: ["hip hop", "trap"]
                - "Heavy metal for workout" → genres: ["metal", "rock"]
                - "Chill indie songs" → genres: ["indie", "alternative"]
                - "90s gangsta rap" → genres: ["90s rap", "hip hop"]
                - "Electronic dance music" → genres: ["electronic", "dance"]

                User request guides output; preferences strongly influence it.
            """

            response_text = await self._call_ai_model(ai_prompt)

            try:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    strategy = json.loads(json_str)

                    if "mood_keywords" in strategy and isinstance(strategy["mood_keywords"], list):
                        return strategy

            except json.JSONDecodeError:
                pass

            return await self._parse_ai_response(response_text, prompt, user_context)

        except Exception as e:
            logger.error(f"AI strategy generation failed: {e}")
            raise RuntimeError(f"AI strategy generation failed: {e}")

    async def _parse_ai_response(self, ai_text: str, prompt: str, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """Parse AI response when JSON extraction fails"""

        mood_keywords = []
        genres = []
        energy_level = "medium"

        text_to_analyze = f"{prompt} {ai_text}".lower()
        mood_patterns = data_loader.get_mood_patterns()

        for mood, keywords in mood_patterns.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                mood_keywords.append(mood)

        genre_patterns = data_loader.get_genre_patterns()

        for genre, keywords in genre_patterns.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                genres.append(genre)

        energy_trigger_words = data_loader.get_energy_trigger_words()

        if any(word in text_to_analyze for word in energy_trigger_words.get("high", [])):
            energy_level = "high"

        elif any(word in text_to_analyze for word in energy_trigger_words.get("low", [])):
            energy_level = "low"

        elif any(word in text_to_analyze for word in energy_trigger_words.get("ultra-high", [])):
            energy_level = "high"

        elif any(word in text_to_analyze for word in energy_trigger_words.get("ultra-low", [])):
            energy_level = "low"

        activity_patterns = data_loader.get_activity_patterns()
        activity_energy_mapping = data_loader.get_activity_energy_mapping()

        for activity, keywords in activity_patterns.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                if activity in activity_energy_mapping:
                    mapped_energy = activity_energy_mapping[activity]

                    if mapped_energy in ["ultra-low", "ultra-high"]:
                        energy_level = "low" if mapped_energy == "ultra-low" else "high"

                    else:
                        energy_level = mapped_energy

                    break

        time_contexts = data_loader.get_time_contexts()

        for time_period, keywords in time_contexts.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                mood_keywords.append(time_period)
                break

        emotion_intensities = data_loader.get_emotion_intensities()

        for intensity_level, modifiers in emotion_intensities.items():
            if any(modifier in text_to_analyze for modifier in modifiers):
                if intensity_level == "extreme" and energy_level == "medium":
                    energy_level = "high"

                elif intensity_level == "mild" and energy_level == "high":
                    energy_level = "medium"

                break

        if user_context:
            if user_context.favorite_genres:
                genres.extend(user_context.favorite_genres[:2])

            if user_context.energy_preference:
                energy_level = user_context.energy_preference

        if not mood_keywords:
            mood_keywords = ["upbeat", "popular"]

        if not genres:
            genres = ["pop", "indie"]

        return {
            "mood_keywords": mood_keywords[:5],
            "genres": genres[:3],
            "energy_level": energy_level,
            "explanation": f"Generated strategy for: {prompt}"
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
