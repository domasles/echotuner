"""
Playlist generator service.
Generates playlists using AI-powered real-time song search.
"""

import logging
import httpx
import random
import json

from typing import List, Dict, Any, Optional

from core.singleton import SingletonServiceBase
from core.models import Song, UserContext

from config.ai_models import ai_model_manager
from config.settings import settings

from services.spotify_search_service import spotify_search_service
from services.data_service import data_loader

logger = logging.getLogger(__name__)

class PlaylistGeneratorService(SingletonServiceBase):
    """AI service that generates playlists using real-time song search."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the PlaylistGeneratorService."""

        self.spotify_search = spotify_search_service
        self.model_config = ai_model_manager.get_provider()
        self.http_client = None

        self._log_initialization("Playlist generator service initialized successfully", logger)

    async def initialize(self):
        """Initialize the AI model and Spotify search service"""

        try:
            self.http_client = httpx.AsyncClient(timeout=self.model_config.timeout)
            await self.spotify_search.initialize()

            if not await self._check_ai_model_connection():
                logger.error(f"AI model {self.model_config.name} not running or not accessible")
                raise RuntimeError(f"AI model {self.model_config.name} is not accessible. Please check your configuration.")

            await self._ensure_model_available()

            logger.info(f"AI Playlist Generation initialized successfully with {self.model_config.name}!")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Playlist generation initialization failed: {e}")
            raise RuntimeError(f"Playlist generation initialization failed: {e}")

    async def _check_ai_model_connection(self) -> bool:
        """Check if the AI model is running and accessible"""

        try:
            if self.model_config.name.lower() == "ollama":
                response = await self.http_client.get(f"{self.model_config.endpoint}/api/tags")
                return response.status_code == 200

            else:
                return (self.model_config.endpoint is not None)

        except:
            return False

    async def _ensure_model_available(self):
        """Ensure the required model is available"""

        try:
            if self.model_config.name.lower() == "ollama":
                response = await self.http_client.get(f"{self.model_config.endpoint}/api/tags")

                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in models]

                    if self.model_config.generation_model not in model_names:
                        logger.info(f"Model {self.model_config.generation_model} not found, pulling...")
                        await self._pull_model()

                    else:
                        logger.info(f"Model {self.model_config.generation_model} is available")

            else:
                logger.info(f"Using external AI model: {self.model_config.name}")

        except Exception as e:
            logger.error(f"Model check failed: {e}")
            raise RuntimeError(f"Model check failed: {e}")

    async def _pull_model(self):
        """Pull the required model (Ollama only)"""

        try:
            if self.model_config.name.lower() != "ollama":
                return

            response = await self.http_client.post(
                f"{self.model_config.endpoint}/api/pull",
                json={"name": self.model_config.generation_model},
                timeout=settings.AI_MODEL_PULL_TIMEOUT
            )

            if response.status_code == 200:
                logger.info(f"Model {self.model_config.generation_model} pulled successfully")

            else:
                logger.error(f"Failed to pull model {self.model_config.generation_model}")
                raise RuntimeError(f"Failed to pull model {self.model_config.generation_model}")

        except Exception as e:
            logger.error(f"Model pull failed: {e}")
            raise RuntimeError(f"Model pull failed: {e}")

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
            search_strategy = await self._generate_search_strategy(prompt, user_context, discovery_strategy)

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

    async def _generate_search_strategy(self, prompt: str, user_context: Optional[UserContext] = None, discovery_strategy: str = "balanced") -> Dict[str, Any]:
        """
        Use AI to analyze the prompt and generate a search strategy.

        Returns:
            Dictionary with mood_keywords, genres, energy_level, etc.
        """

        if not await self._check_ai_model_connection():
            raise RuntimeError("AI model connection lost during playlist generation")

        return await self._ai_generate_strategy(prompt, user_context)

    async def _ai_generate_strategy(self, prompt: str, user_context: Optional[UserContext] = None, discovery_strategy: str = "balanced") -> Dict[str, Any]:
        """Generate search strategy using AI model"""

        try:
            context = f"User prompt: {prompt}\n\n"
            context += "CRITICAL CONSTRAINTS:\n"

            if user_context:
                if user_context.disliked_artists:
                    context += f"NEVER INCLUDE songs by these artists (user explicitly dislikes them): {', '.join(user_context.disliked_artists)}\n"
                    context += f"STRICTLY FORBIDDEN artists that must be avoided at ALL COSTS: {', '.join(user_context.disliked_artists)}\n"
                    context += f"Before recommending ANY song, verify the artist is NOT in this list: {', '.join(user_context.disliked_artists)}\n\n"

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

    async def refine_playlist(self, original_songs: List[Song], refinement_prompt: str, user_context: Optional[UserContext] = None, count: int = 30, discovery_strategy: str = "balanced") -> List[Song]:
        """Refine an existing playlist based on user feedback with improved accuracy."""

        try:
            search_strategy = await self._generate_search_strategy(refinement_prompt, user_context, discovery_strategy)
            refinement_type = await self._analyze_refinement_type(refinement_prompt)
            
            if refinement_type == "replace_all":
                return await self._generate_new_playlist(search_strategy, count, user_context)

            elif refinement_type == "add_similar":
                return await self._expand_similar_songs(original_songs, search_strategy, count, user_context)

            elif refinement_type == "adjust_mood":
                return await self._adjust_playlist_mood(original_songs, search_strategy, count, user_context)

            else:
                return await self._smart_mix_refinement(original_songs, search_strategy, count, user_context)

        except Exception as e:
            logger.error(f"Playlist refinement failed: {e}")
            raise RuntimeError(f"Playlist refinement failed: {e}")

    async def _analyze_refinement_type(self, refinement_prompt: str) -> str:
        """Analyze the refinement prompt to determine the best approach."""

        prompt_lower = refinement_prompt.lower()
        replace_keywords = ["different", "change all", "completely new", "start over", "hate these", "don't like any"]

        if any(keyword in prompt_lower for keyword in replace_keywords):
            return "replace_all"

        similar_keywords = ["more like this", "similar", "same style", "keep going", "more of the same"]

        if any(keyword in prompt_lower for keyword in similar_keywords):
            return "add_similar"

        mood_keywords = ["more energetic", "calmer", "happier", "sadder", "more upbeat", "more mellow", "faster", "slower"]

        if any(keyword in prompt_lower for keyword in mood_keywords):
            return "adjust_mood"

        return "smart_mix"

    async def _generate_new_playlist(self, search_strategy: Dict[str, Any], count: int, user_context: Optional[UserContext]) -> List[Song]:
        """Generate completely new songs based on refinement."""

        new_songs = await self.spotify_search.search_songs_by_mood(
            mood_keywords=search_strategy["mood_keywords"],
            genres=search_strategy.get("genres"),
            energy_level=search_strategy.get("energy_level"),
            count=count + 10
        )

        if user_context and user_context.disliked_artists:
            disliked_artists_lower = [artist.lower() for artist in user_context.disliked_artists]

            new_songs = [
                song for song in new_songs 
                if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower)
            ]

        random.shuffle(new_songs)
        return new_songs[:count]

    async def _expand_similar_songs(self, original_songs: List[Song], search_strategy: Dict[str, Any], count: int, user_context: Optional[UserContext]) -> List[Song]:
        """Keep most original songs and add similar ones."""

        keep_count = int(count * 0.7)
        new_count = count - keep_count
        kept_songs = original_songs[:keep_count] if original_songs else []
        original_artists = list(set([song.artist for song in kept_songs]))
        enhanced_strategy = search_strategy.copy()
        enhanced_strategy["favorite_artists"] = (enhanced_strategy.get("favorite_artists", []) + original_artists)[:10]

        new_songs = await self.spotify_search.search_songs_by_mood(
            mood_keywords=enhanced_strategy["mood_keywords"],
            genres=enhanced_strategy.get("genres"),
            energy_level=enhanced_strategy.get("energy_level"),
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
        return final_songs[:count]

    async def _adjust_playlist_mood(self, original_songs: List[Song], search_strategy: Dict[str, Any], count: int, user_context: Optional[UserContext]) -> List[Song]:
        """Adjust the mood/energy while keeping some original songs."""

        keep_count = int(count * 0.4)
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

        random.shuffle(final_songs)
        return final_songs[:count]

    async def _smart_mix_refinement(self, original_songs: List[Song], search_strategy: Dict[str, Any], count: int, user_context: Optional[UserContext]) -> List[Song]:
        """Default smart mix approach - balanced refinement."""

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
            additional_songs = await self._get_additional_songs(final_songs, count, search_strategy)
            final_songs.extend(additional_songs[:additional_needed])

        random.shuffle(final_songs)
        return final_songs[:count]

    async def _call_ai_model(self, prompt: str) -> str:
        """Universal method to call different AI models"""

        if self.model_config.name.lower() == "ollama":
            response = await self.http_client.post(
                f"{self.model_config.endpoint}/api/generate",
                json={
                    "model": self.model_config.generation_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.model_config.timeout
            )

            if response.status_code == 200:
                return response.json()["response"].strip()

            else:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

        elif self.model_config.name.lower() == "openai":
            headers = self.model_config.headers or {}

            data = {
                "model": self.model_config.generation_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.model_config.max_tokens,
                "temperature": self.model_config.temperature
            }

            response = await self.http_client.post(
                f"{self.model_config.endpoint}/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()

            else:
                raise Exception(f"OpenAI API error: {response.status_code}")

        elif self.model_config.name.lower() == "anthropic":
            headers = self.model_config.headers or {}

            data = {
                "model": self.model_config.generation_model,
                "max_tokens": self.model_config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.model_config.temperature
            }

            response = await self.http_client.post(
                f"{self.model_config.endpoint}/v1/messages",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"].strip()

            else:
                raise Exception(f"Anthropic API error: {response.status_code}")

        else:
            raise Exception(f"Unsupported AI model: {self.model_config.name}")

playlist_generator_service = PlaylistGeneratorService()
