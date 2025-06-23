import requests
import asyncio
import logging

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

    async def initialize(self):
        """Initialize the AI model and Spotify search service"""
        
        try:
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
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=settings.OLLAMA_TIMEOUT)
            return response.status_code == 200

        except:
            return False
    
    async def _ensure_model_available(self):
        """Ensure the required model is available"""

        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")

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
            response = requests.post(
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
                    context += f"Favorite genres: {', '.join(user_context.favorite_genres)}\n"

                if user_context.favorite_artists:
                    context += f"Favorite artists: {', '.join(user_context.favorite_artists)}\n"

                if user_context.energy_preference:
                    context += f"Energy preference: {user_context.energy_preference}\n"   

            genre_patterns = data_loader.get_genre_patterns()
            activity_patterns = data_loader.get_activity_patterns()
            activity_energy_mapping = data_loader.get_activity_energy_mapping()
            mood_patterns = data_loader.get_mood_patterns()

            available_genres = list(genre_patterns.keys())
            available_activities = list(activity_patterns.keys())
            activity_energies = {k: v for k, v in activity_energy_mapping.items() if k in available_activities}
            available_moods = list(mood_patterns.keys())

            ai_prompt = f"""
                Analyze this music request and generate search keywords:
                {context}

                Available genres: {', '.join(available_genres)}
                Available activities: {', '.join(available_activities)}
                Activity energy mappings: {activity_energies}
                Available moods: {', '.join(available_moods)}

                Based on this request and the available data above, provide:
                1. 3-5 mood keywords for searching songs
                2. 2-3 relevant music genres (use the available genres list above)
                3. Energy level (low/medium/high) - consider activity energy mappings
                4. Brief explanation of the mood

                Format your response as JSON:
                {{
                    "mood_keywords": ["keyword1", "keyword2", "keyword3"],
                    "genres": ["genre1", "genre2"],
                    "energy_level": "medium",
                    "explanation": "Brief description of the mood"
                }}

                Examples:
                - "I'm feeling sad and nostalgic" → {{"mood_keywords": ["sad", "melancholy", "nostalgic"], "genres": ["ballad", "alternative"], "energy_level": "low"}}
                - "Need pump up music for gym" → {{"mood_keywords": ["energetic", "pump up", "workout"], "genres": ["hip hop", "rock"], "energy_level": "high"}}
                - "Chill study music" → {{"mood_keywords": ["chill", "calm", "focus"], "genres": ["ambient", "lo-fi"], "energy_level": "low"}}
                - "I need something close to 90s rap for my deep coding session" → {{"mood_keywords": ["focus", "coding", "90s", "nostalgic"], "genres": ["90s rap", "hip hop"], "energy_level": "low"}}
                - "Play some classic rock from the 70s for my workout" → {{"mood_keywords": ["workout", "classic", "energetic"], "genres": ["70s", "classic rock"], "energy_level": "high"}}
                - "I want lo-fi hip hop for concentration" → {{"mood_keywords": ["concentration", "chill", "focus"], "genres": ["lo-fi", "hip hop"], "energy_level": "low"}}
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
