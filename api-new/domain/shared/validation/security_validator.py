"""Security validation for API requests to prevent abuse"""

import logging
from typing import Any, List, Optional
from fastapi import HTTPException
from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Validates request content to prevent API abuse"""
    
    @staticmethod
    def validate_user_context_size(user_context: Any) -> None:
        """Validate user context content and nested artist limits"""
        if user_context is None:
            return
            
        try:
            # Check for nested artist arrays with specific limits
            context_dict = user_context.dict() if hasattr(user_context, 'dict') else user_context
            if isinstance(context_dict, dict) and 'context' in context_dict:
                inner_context = context_dict['context']
                if isinstance(inner_context, dict):
                    # Validate favorite artists with specific limit
                    if 'favorite_artists' in inner_context:
                        artists = inner_context['favorite_artists']
                        if isinstance(artists, list) and len(artists) > settings.MAX_FAVORITE_ARTISTS:
                            logger.warning(f"Favorite artists count {len(artists)} exceeds limit {settings.MAX_FAVORITE_ARTISTS}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"Too many favorite artists. Maximum: {settings.MAX_FAVORITE_ARTISTS}"
                            )
                    
                    # Validate disliked artists with specific limit
                    if 'disliked_artists' in inner_context:
                        artists = inner_context['disliked_artists']
                        if isinstance(artists, list) and len(artists) > settings.MAX_DISLIKED_ARTISTS:
                            logger.warning(f"Disliked artists count {len(artists)} exceeds limit {settings.MAX_DISLIKED_ARTISTS}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"Too many disliked artists. Maximum: {settings.MAX_DISLIKED_ARTISTS}"
                            )
                        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to validate user context: {e}")
            raise HTTPException(status_code=400, detail="Invalid user context format")
    
    @staticmethod
    def validate_string_length(value: str, max_length: int, field_name: str) -> None:
        """Validate string field length"""
        if len(value) > max_length:
            logger.warning(f"{field_name} length {len(value)} exceeds limit {max_length}")
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} too long. Maximum length: {max_length}"
            )
