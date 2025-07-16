"""
Vector embedding cache for AI responses using database storage.
Database-based caching with standardized patterns and error handling.
"""

import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.singleton import SingletonServiceBase
from core.service_manager import ServiceManager
from config.app_constants import AppConstants
from core.validation.validators import UniversalValidator
from utils.exceptions import handle_service_errors, raise_ai_error, ErrorCode

from database.core import get_session
from database.models import EmbeddingCache
from sqlalchemy.future import select
from sqlalchemy import and_, delete, update, func

logger = logging.getLogger(__name__)

class EmbeddingCacheService(SingletonServiceBase):
    """Manages vector embedding cache for AI responses using database storage."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize embedding cache service."""
        
        self._log_initialization("Embedding cache service initialized with database storage", logger)

    async def initialize(self):
        """Initialize the embedding cache service."""
        # No file loading needed - using database
        pass

    def _generate_cache_key(self, prompt: str, user_context: Optional[str] = None) -> str:
        """Generate a unique cache key for the given prompt and context."""
        try:
            input_data = prompt
            if user_context:
                input_data += f"|{user_context}"
            
            return hashlib.sha256(input_data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            return ""

    @handle_service_errors("get_cached_embedding")
    async def get_cached_embedding(self, prompt: str, user_context: Optional[str] = None) -> Optional[Any]:
        """Get cached embedding for the given prompt and context using standardized operations."""
        try:
            cache_key = self._generate_cache_key(prompt, user_context)
            if not cache_key:
                raise_ai_error("Failed to generate cache key", ErrorCode.AI_EMBEDDING_FAILED)

            # Use session directly instead of mixin method
            async with get_session() as session:
                from database.models import EmbeddingCache
                result = await session.execute(
                    select(EmbeddingCache).where(EmbeddingCache.cache_key == cache_key)
                )
                cached_entry = result.scalar_one_or_none()

                if cached_entry:
                    logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                    return cached_entry.response_data
                    
            logger.debug(f"Cache miss for key: {cache_key[:16]}...")
            return None
            
        except Exception as e:
            raise_ai_error(f"Failed to get cached embedding: {e}", ErrorCode.AI_EMBEDDING_FAILED)

    @handle_service_errors("store_embedding")
    async def store_embedding(self, prompt: str, response: Any, user_context: Optional[str] = None) -> bool:
        """Store embedding in cache using standardized operations."""
        try:
            cache_key = self._generate_cache_key(prompt, user_context)
            if not cache_key:
                raise_ai_error("Failed to generate cache key", ErrorCode.AI_EMBEDDING_FAILED)

            # Use session directly instead of mixin method
            async with get_session() as session:
                from database.models import EmbeddingCache
                cache_entry = EmbeddingCache(
                    cache_key=cache_key,
                    prompt=prompt,
                    response_data=response,
                    user_context=user_context,
                    created_at=datetime.now().isoformat(),
                    last_accessed=datetime.now().isoformat(),
                    access_count=1
                )
                
                session.add(cache_entry)
                await session.commit()
                
            logger.debug(f"Stored embedding for key: {cache_key[:16]}...")
            return True
            
        except Exception as e:
            raise_ai_error(f"Failed to store embedding: {e}", ErrorCode.AI_EMBEDDING_FAILED)

        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            return False

    async def update_access_count(self, prompt: str, user_context: Optional[str] = None) -> bool:
        """Update access count for cached entry."""
        try:
            cache_key = self._generate_cache_key(prompt, user_context)
            if not cache_key:
                return False

            async with get_session() as session:
                await session.execute(
                    update(EmbeddingCache)
                    .where(EmbeddingCache.cache_key == cache_key)
                    .values(
                        access_count=EmbeddingCache.access_count + 1,
                        last_accessed=datetime.now().isoformat()
                    )
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to update access count: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            async with get_session() as session:
                total_entries_result = await session.execute(
                    select(func.count(EmbeddingCache.cache_key))
                )
                total_entries = total_entries_result.scalar() or 0

                total_access_result = await session.execute(
                    select(func.sum(EmbeddingCache.access_count))
                )
                total_access_count = total_access_result.scalar() or 0
                
                return {
                    "total_entries": total_entries,
                    "total_access_count": total_access_count,
                    "storage_type": "database"
                }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": UniversalValidator.sanitize_error_message(str(e))}

    async def clear_cache(self) -> bool:
        """Clear all cache entries."""
        try:
            async with get_session() as session:
                await session.execute(delete(EmbeddingCache))
                await session.commit()
                logger.info("Embedding cache cleared")
                return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def remove_cache_entry(self, prompt: str, user_context: Optional[str] = None) -> bool:
        """Remove specific cache entry."""
        try:
            cache_key = self._generate_cache_key(prompt, user_context)
            if not cache_key:
                return False

            async with get_session() as session:
                result = await session.execute(
                    delete(EmbeddingCache).where(EmbeddingCache.cache_key == cache_key)
                )
                await session.commit()
                
                if result.rowcount > 0:
                    logger.debug(f"Removed cache entry for key: {cache_key[:16]}...")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to remove cache entry: {e}")
            return False

    async def get_cache_size(self) -> int:
        """Get the number of entries in the cache."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(func.count(EmbeddingCache.cache_key))
                )
                return result.scalar() or 0

        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return 0

# Create singleton instance
embedding_cache_service = EmbeddingCacheService()
