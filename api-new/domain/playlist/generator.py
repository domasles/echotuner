"""
Playlist generator service.
Generates playlists using AI-powered real-time song search.
"""

import logging
import random
import json

from typing import List, Dict, Any, Optional

from application.core.singleton import SingletonServiceBase
from application import Song, UserContext
from infrastructure.config.settings import settings
from infrastructure.config.app_constants import app_constants

from infrastructure.spotify.service import spotify_search_service
from infrastructure.data.service import data_loader
from domain.ai.service import ai_service
from domain.personality.service import personality_service

from domain.shared.validation.validators import UniversalValidator

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

            # Get enhanced personality context if user_id provided
            enhanced_prompt = prompt
            if user_id:
                enhanced_prompt = await personality_service.get_personality_enhanced_context_by_user_id(
                    user_id=user_id, 
                    prompt=prompt
                )

            # AI-powered real song lookup - OPTIMIZED: Single call with higher count
            target_count = min(count + 10, settings.MAX_SONGS_PER_PLAYLIST)  # Request slightly more for better filtering
            songs = await self._ai_lookup_real_songs(enhanced_prompt, user_context, discovery_strategy, target_count, original_prompt=prompt)
            
            if not songs:
                logger.warning("AI song lookup returned no results")
                return []

            # Filter out disliked artists if any
            if user_context and user_context.disliked_artists:
                disliked_artists_lower = [artist.lower() for artist in user_context.disliked_artists]
                filtered_songs = []

                for song in songs:
                    if not any(disliked.lower() in song.artist.lower() for disliked in disliked_artists_lower):
                        filtered_songs.append(song)

                songs = filtered_songs

            # Final shuffle and return exact count
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
            
            # Add user preferences
            if user_context:
                if user_context.favorite_genres:
                    context_parts.append(f"Favorite genres: {', '.join(user_context.favorite_genres[:settings.MAX_FAVORITE_GENRES])}")
                if user_context.favorite_artists:
                    context_parts.append(f"Favorite artists: {', '.join(user_context.favorite_artists[:settings.MAX_FAVORITE_ARTISTS])}")
                if user_context.decade_preference:
                    context_parts.append(f"Preferred decades: {', '.join(user_context.decade_preference[:settings.MAX_PREFERRED_DECADES])}")
                if user_context.disliked_artists:
                    context_parts.append(f"Avoid these artists: {', '.join(user_context.disliked_artists[:settings.MAX_DISLIKED_ARTISTS])}")
            
            # Strategy-specific instructions
            if discovery_strategy == "existing_music":
                instruction = "Focus on popular, well-known songs from the user's preferred genres and decades. Include classics and hits."
            elif discovery_strategy == "new_music":
                instruction = "Focus on lesser-known gems, underground artists, and hidden tracks from the preferred genres and decades."
            else:
                instruction = "Mix popular classics with some hidden gems and lesser-known tracks."
            
            # Create AI prompt for real song lookup - OPTIMIZED: Only title and artist to save tokens
            ai_prompt = f"""
{chr(10).join(context_parts)}

{instruction}

Please provide {count} real songs that match this request. Return ONLY a JSON array of songs in this exact format:
[
  {{"title": "Song Title", "artist": "Artist Name"}},
  {{"title": "Song Title", "artist": "Artist Name"}}
]

Requirements:
- All songs must be REAL songs that exist
- Match the user's mood and preferences
- Include variety across the preferred genres and decades
- No explanations, just the JSON array
"""

            response_text = await self._call_ai_model(ai_prompt)
            
            # Parse AI response
            songs = await self._parse_ai_song_response(response_text)
            
            if not songs:
                logger.warning("AI song lookup returned no results")
                return []
            
            # Verify songs exist on Spotify and get full metadata
            verified_songs = await self._verify_songs_on_spotify(songs)
            
            logger.info(f"AI suggested {len(songs)} songs, {len(verified_songs)} verified on Spotify")
            return verified_songs
            
        except Exception as e:
            logger.error(f"AI song lookup failed: {e}")
            return []  # Return empty list to trigger fallback
    
    async def _parse_ai_song_response(self, response_text: str) -> List[dict]:
        """Parse AI response containing song suggestions"""
        
        try:
            # Find JSON array in response
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                songs_data = json.loads(json_str)
                
                # Validate structure
                if isinstance(songs_data, list) and len(songs_data) > 0:
                    valid_songs = []
                    for song in songs_data:
                        if isinstance(song, dict) and "title" in song and "artist" in song:
                            valid_songs.append(song)
                    
                    return valid_songs
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI song response: {e}")
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
            return await ai_service.generate_text(prompt, model_id=None)

        except Exception as e:
            logger.error(f"AI model call failed: {e}")
            raise RuntimeError(f"AI model call failed: {e}")

playlist_generator_service = PlaylistGeneratorService()
