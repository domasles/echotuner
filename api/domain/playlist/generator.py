"""
Playlist generator service.
Generates playlists using AI-powered real-time song search.
"""

import logging
import random
import json

from typing import List, Dict, Any, Optional

from infrastructure.singleton import SingletonServiceBase
from application import Song, UserContext
from domain.config.settings import settings
from domain.config.app_constants import app_constants

from infrastructure.spotify.service import spotify_search_service
from infrastructure.ai.registry import provider_registry
from infrastructure.personality.service import personality_service

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class PlaylistGeneratorService(SingletonServiceBase):
    """AI service that generates playlists using real-time song search."""

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the PlaylistGeneratorService."""

        self.spotify_search = spotify_search_service

    async def generate_playlist(self, prompt: str, user_context: Optional[UserContext] = None, count: int = 30, discovery_strategy: str = "balanced", user_id: str = None) -> List[Song]:
        """
        Generate a playlist using AI-powered real-time song search with full personality context.

        Args:
            prompt: User's mood/context description
            user_context: Additional user preferences
            count: Number of songs to generate
            discovery_strategy: "new_music", "existing_music", or "balanced"
            user_id: User ID for personality data

        Returns:
            List of exactly 'count' songs
        """

        try:
            prompt = UniversalValidator.validate_prompt(prompt)
            count = UniversalValidator.validate_count(count, min_count=1, max_count=100)

            if discovery_strategy not in ["new_music", "existing_music", "balanced"]:
                discovery_strategy = "balanced"

            target_count = min(count + 10, settings.MAX_SONGS_PER_PLAYLIST)  # Request slightly more for better filtering
            songs = await self._ai_lookup_real_songs(prompt, user_context, discovery_strategy, target_count, original_prompt=prompt)
            
            if not songs:
                logger.warning("AI song lookup returned no results")
                return []
            random.shuffle(songs)
            songs = songs[:count]

            if len(songs) < count:
                logger.warning(f"Generated only {len(songs)} songs instead of requested {count}. This may happen with AI-based generation or filtering.")

            logger.debug(f"Generated {len(songs)} songs using AI-powered lookup (requested: {count})")
            return songs

        except ValueError as e:
            logger.warning(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input: {e}")

        except Exception as e:
            logger.error(f"Playlist generation failed: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Playlist generation failed: {sanitized_error}")

    async def _ai_lookup_real_songs(self, prompt: str, user_context: Optional[UserContext] = None, discovery_strategy: str = "balanced", count: int = 30, original_prompt: str = None) -> List[Song]:
        """AI-powered real song lookup - generates actual songs from training data"""
        
        try:
            # Use original prompt for song lookup if available
            prompt_for_lookup = original_prompt or prompt
            
            # Build context for AI song lookup
            context_parts = [f"User request: {prompt_for_lookup}"]
            
            # Add user preferences as raw JSON from app
            if user_context and user_context.context:
                context_parts.append(f"User preferences: {json.dumps(user_context.context)}")
            
            # Strategy-specific instructions
            if discovery_strategy == "existing_music":
                instruction = "Focus on popular, well-known songs from the user's preferred genres and decades. Include classics and hits."
            elif discovery_strategy == "new_music":
                instruction = "Focus on lesser-known gems, underground artists, and hidden tracks from the preferred genres and decades."
            else:
                instruction = "Mix popular classics with some hidden gems and lesser-known tracks."

            ai_prompt = f"""
{chr(10).join(context_parts)}

{instruction}

Return exactly {count} REAL songs as a JSON array in this format:
[{{"title": "Song Title", "artist": "Artist Name"}}]

Constraints:
- All songs must exist in the real world
- No duplicate songs
- Match the user's mood and preferences
- Ensure variety across genres and decades
- Output JSON ONLY, no text before or after
"""

            response_text = await self._call_ai_model(ai_prompt)
            
            # Parse AI response
            songs = await self._parse_ai_song_response(response_text)
            
            if not songs:
                logger.warning("AI song lookup returned no results")
                return []
            
            # Verify songs exist on Spotify and get full metadata
            verified_songs = await self._verify_songs_on_spotify(songs)
            
            logger.debug(f"AI suggested {len(songs)} songs, {len(verified_songs)} verified on Spotify")
            return verified_songs
            
        except Exception as e:
            logger.error(f"AI song lookup failed: {e}")
            return []  # Return empty list to trigger fallback
    
    async def _parse_ai_song_response(self, response_text: str) -> List[dict]:
        """Parse AI response containing song suggestions"""
        
        try:
            # Clean up the response text
            response_text = response_text.strip()
            
            # Find JSON array in response
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                
                # Clean up common JSON issues
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                json_str = ' '.join(json_str.split())  # Remove extra whitespace
                
                # Try to fix common JSON formatting issues
                # Remove trailing commas before closing brackets
                json_str = json_str.replace(',]', ']').replace(',}', '}')
                
                songs_data = json.loads(json_str)
                
                # Validate structure
                if isinstance(songs_data, list) and len(songs_data) > 0:
                    valid_songs = []
                    for song in songs_data:
                        if isinstance(song, dict) and "title" in song and "artist" in song:
                            # Clean up song data
                            clean_song = {
                                "title": str(song["title"]).strip(),
                                "artist": str(song["artist"]).strip()
                            }
                            if clean_song["title"] and clean_song["artist"]:
                                valid_songs.append(clean_song)
                    
                    return valid_songs
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI song response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")  # Log first 500 chars for debugging
            return []
    
    async def _verify_songs_on_spotify(self, ai_songs: List[dict]) -> List[Song]:
        """Fast verification of AI-suggested songs on Spotify - OPTIMIZED"""
        
        verified_songs = []
        
        for song_data in ai_songs:
            try:
                # Build search query for exact match - only title and artist needed
                title = song_data.get("title", "").strip()
                artist = song_data.get("artist", "").strip()
                
                if not title or not artist:
                    continue
                
                # Fast exact search with minimal query
                search_query = f'"{title}" "{artist}"'
                
                # Use Spotify's faster search method - single call per song
                songs = await self.spotify_search._search_spotify(search_query, limit=1)
                
                if songs:
                    verified_songs.append(songs[0])
                else:
                    # Quick fallback: just title and artist name without quotes
                    fallback_query = f"{title} {artist}"
                    fallback_songs = await self.spotify_search._search_spotify(fallback_query, limit=1)
                    
                    if fallback_songs:
                        verified_songs.append(fallback_songs[0])
                    
            except Exception as e:
                logger.warning(f"Failed to verify song '{song_data.get('title', 'Unknown')}' by '{song_data.get('artist', 'Unknown')}': {e}")
                continue
        
        return verified_songs

    async def _call_ai_model(self, prompt: str) -> str:
        """Universal method to call different AI models"""

        try:
            return await provider_registry.generate_text(prompt, model_id=None)

        except Exception as e:
            logger.error(f"AI model call failed: {e}")
            raise RuntimeError(f"AI model call failed: {e}")

playlist_generator_service = PlaylistGeneratorService()
