import asyncio
import logging
import httpx

import ollama
import random
import json

from typing import List, Dict, Any, Optional

from services.spotify_search_service import SpotifySearchService
from services.data_loader import data_loader
from core.models import Song, UserContext
from config.settings import settings

logger = logging.getLogger(__name__)

class PlaylistGeneratorService:
    """AI service that generates playlists using real-time song search."""

    def __init__(self):
        self.spotify_search = SpotifySearchService()

        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_GENERATION_MODEL
        self.use_ollama = settings.USE_OLLAMA

        self.initialized = False
        self.http_client = None

    async def initialize(self):
        """Initialize the AI model and Spotify search service"""

        try:
            self.http_client = httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT)
            await self.spotify_search.initialize()

            if not self.use_ollama:
                logger.error("Ollama is required for this application")
                raise RuntimeError("Ollama must be enabled. Set USE_OLLAMA=true in environment variables.")

            if not await self._check_ollama_connection():
                logger.error("Ollama not running or not accessible")
                raise RuntimeError("Ollama is not running. Please start Ollama and try again.")

            await self._ensure_model_available()

            logger.info("AI Playlist Generation initialized successfully!")
            self.initialized = True

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Playlist generation initialization failed: {e}")
            raise RuntimeError(f"Playlist generation initialization failed: {e}")

    def is_ready(self) -> bool:
        """Check if the service is ready"""

        return self.initialized

    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""

        try:
            response = await self.http_client.get(f"{self.ollama_base_url}/api/tags")
            return response.status_code == 200

        except:
            return False

    async def _ensure_model_available(self):
        """Ensure the required model is available"""

        try:
            response = await self.http_client.get(f"{self.ollama_base_url}/api/tags")

            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]

                if self.model_name not in model_names:
                    logger.info(f"Model {self.model_name} not found, pulling...")
                    await self._pull_model()

                else:
                    logger.info(f"Model {self.model_name} is available")

        except Exception as e:
            logger.error(f"Model check failed: {e}")
            raise RuntimeError(f"Model check failed: {e}")

    async def _pull_model(self):
        """Pull the required model"""

        try:
            response = await self.http_client.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": self.model_name},
                timeout=settings.OLLAMA_MODEL_PULL_TIMEOUT
            )

            if response.status_code == 200:
                logger.info(f"Model {self.model_name} pulled successfully")

            else:
                logger.error(f"Failed to pull model {self.model_name}")
                raise RuntimeError(f"Failed to pull model {self.model_name}")

        except Exception as e:
            logger.error(f"Model pull failed: {e}")
            raise RuntimeError(f"Model pull failed: {e}")

    async def generate_playlist(self, prompt: str, user_context: Optional[UserContext] = None, count: int = 30) -> List[Song]:
        """
        Generate a playlist using AI-powered real-time song search.

        Args:
            prompt: User's mood/context description
            user_context: Additional user preferences
            count: Number of songs to generate

        Returns:
            List of exactly 'count' songs
        """

        if not self.initialized:
            await self.initialize()

        try:
            search_strategy = await self._generate_search_strategy(prompt, user_context)

            songs = await self.spotify_search.search_songs_by_mood(
                mood_keywords=search_strategy["mood_keywords"],
                genres=search_strategy.get("genres"),
                energy_level=search_strategy.get("energy_level"),
                user_context=user_context,
                count=count
            )

            if len(songs) < count:
                additional_songs = await self._get_additional_songs(
                    existing_songs=songs, 
                    target_count=count,
                    search_strategy=search_strategy
                )

                songs.extend(additional_songs)

            songs = songs[:count]

            if user_context and user_context.disliked_artists:
                disliked_artists_lower = [artist.lower() for artist in user_context.disliked_artists]
                filtered_songs = []

                for song in songs:
                    if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower):
                        filtered_songs.append(song)

                if len(filtered_songs) < count * 0.8:
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

                songs = filtered_songs[:count]

            random.shuffle(songs)

            logger.info(f"Generated {len(songs)} songs using AI + Spotify search")
            return songs

        except Exception as e:
            logger.error(f"Playlist generation failed: {e}")
            raise RuntimeError(f"Playlist generation failed: {e}")

    async def _generate_search_strategy(self, prompt: str, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """
        Use AI to analyze the prompt and generate a search strategy.

        Returns:
            Dictionary with mood_keywords, genres, energy_level, etc.
        """

        if not await self._check_ollama_connection():
            raise RuntimeError("Ollama connection lost during playlist generation")

        return await self._ai_generate_strategy(prompt, user_context)

    async def _ai_generate_strategy(self, prompt: str, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """Generate search strategy using Ollama AI"""

        try:
            context = f"User prompt: {prompt}\n"

            if user_context:
                if user_context.favorite_genres:
                    context += f"User's favorite genres: {', '.join(user_context.favorite_genres)}\n"

                if user_context.favorite_artists:
                    context += f"User's favorite artists: {', '.join(user_context.favorite_artists)}\n"
                
                if user_context.disliked_artists:
                    context += f"CRITICAL: NEVER include songs by these artists (user explicitly dislikes them): {', '.join(user_context.disliked_artists)}\n"
                    context += f"Double-check every song recommendation to ensure none are by: {', '.join(user_context.disliked_artists)}\n"

                if user_context.energy_preference:
                    context += f"Energy preference: {user_context.energy_preference}\n"

                if user_context.decade_preference:
                    context += f"Preferred decades: {', '.join(user_context.decade_preference)}\n"

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
                    context += f"User's mood preferences: {'; '.join(mood_preferences)}\n"


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
                You are an expert music curator and recommendation AI with deep knowledge of artists, genres, and musical styles. Your primary goal is to deeply understand the user's musical intent and provide recommendations that perfectly match their request, preferences, and personality.

                User Request to analyze:
                {context}

                You have access to the following predefined options:

                - Available genres with representative artists: {', '.join(genre_examples.values())}
                - Available activities: {', '.join(available_activities)}
                - Activity-to-energy mappings: {activity_energies}
                - Available moods: {', '.join(available_moods)}

                CRITICAL INSTRUCTIONS:

                1. **GENRE ACCURACY IS PARAMOUNT**: 
                   - Use the artist examples to understand what each genre truly represents
                   - Hip hop/rap requests should ONLY get hip hop, trap, or rap-related genres
                   - Pop requests should ONLY get pop, dance pop, or mainstream genres
                   - Rock requests should ONLY get rock, alternative, metal, etc.
                   - NEVER mix incompatible genres (e.g., don't suggest pop artists for rap requests)

                2. **ARTIST RECOGNITION**: 
                   - All artist names mentioned in user requests are music-related by definition
                   - If a user mentions ANY artist name, treat it as a valid music reference
                   - Use the artist examples to identify which genre each artist belongs to
                   - Respect the user's artist preferences completely

                3. **USER PERSONALITY INTEGRATION**:
                   - STRICTLY RESPECT user's favorite genres and artists mentioned in their profile
                   - ABSOLUTELY AVOID any artists mentioned in the "AVOID these artists" list
                   - Consider the user's mood preferences for different situations
                   - Respect their discovery openness level (1-10 scale)
                   - Consider their decade preferences when applicable
                   - Honor their explicit content and instrumental music preferences
                   - Factor in their listening context preferences

                4. **ENERGY AND MOOD MAPPING**:
                   - Match energy levels precisely to the request and user activity
                   - Consider the emotional context deeply
                   - Factor in time of day, activity, and user's current state

                Return the following analysis in JSON format:

                1. **mood_keywords**: 3 to 5 strong emotional or stylistic keywords that capture the feeling of the request
                2. **genres**: 2 to 3 genres STRICTLY from the provided genre list that most accurately match the request and user preferences
                3. **energy_level**: "low", "medium", or "high" based on request, activity mapping, and user context
                4. **explanation**: Clear explanation (2-3 sentences) of your analysis, including how user preferences influenced your choices

                Format your response in valid JSON:
                {{
                    "mood_keywords": ["keyword1", "keyword2", "keyword3"],
                    "genres": ["genre1", "genre2"],
                    "energy_level": "medium",
                    "explanation": "Detailed explanation here including user preference considerations"
                }}

                EXAMPLES OF CORRECT GENRE MAPPING:

                - "I want some rap music" → genres: ["hip hop", "trap"] (NOT pop or other genres)
                - "Play some Taylor Swift vibes" → genres: ["pop", "indie pop"] (NOT hip hop)
                - "Heavy metal for working out" → genres: ["metal", "rock"] (NOT electronic)
                - "Chill indie songs" → genres: ["indie", "alternative"] (NOT hip hop or pop)
                - "90s gangsta rap" → genres: ["90s rap", "hip hop"] (NOT alternative rock)
                - "Electronic dance music" → genres: ["electronic", "dance"] (NOT rock or folk)

                Remember: The user's request is the primary guide, but their saved preferences should strongly influence your final recommendations.
            """

            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model_name,
                prompt=ai_prompt
            )

            ai_text = response["response"].strip()

            try:
                start_idx = ai_text.find("{")
                end_idx = ai_text.rfind("}") + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = ai_text[start_idx:end_idx]
                    strategy = json.loads(json_str)

                    if "mood_keywords" in strategy and isinstance(strategy["mood_keywords"], list):
                        return strategy

            except json.JSONDecodeError:
                pass

            return await self._parse_ai_response(ai_text, prompt, user_context)

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

    async def refine_playlist(self, original_songs: List[Song], refinement_prompt: str, user_context: Optional[UserContext] = None, count: int = 30) -> List[Song]:
        """Refine an existing playlist based on user feedback."""

        try:
            search_strategy = await self._generate_search_strategy(refinement_prompt, user_context)

            keep_count = count // 2
            new_count = count - keep_count

            kept_songs = original_songs[:keep_count] if original_songs else []

            new_songs = await self.spotify_search.search_songs_by_mood(
                mood_keywords=search_strategy["mood_keywords"],
                genres=search_strategy.get("genres"),
                energy_level=search_strategy.get("energy_level"),
                count=new_count + 10
            )

            filtered_new_songs = [s for s in new_songs if s not in kept_songs]

            if user_context and user_context.disliked_artists:
                disliked_artists_lower = [artist.lower() for artist in user_context.disliked_artists]
                filtered_new_songs = [
                    song for song in filtered_new_songs 
                    if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower)
                ]

            final_songs = kept_songs + filtered_new_songs[:new_count]

            if len(final_songs) < count:
                additional_needed = count - len(final_songs)
                additional_songs = await self._get_additional_songs(
                    final_songs, count, search_strategy
                )

                final_songs.extend(additional_songs[:additional_needed])

            random.shuffle(final_songs)
            return final_songs[:count]

        except Exception as e:
            logger.error(f"Playlist refinement failed: {e}")
            raise RuntimeError(f"Playlist refinement failed: {e}")
