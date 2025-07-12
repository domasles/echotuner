"""
Embedding cache service.
Manages cached embedding vectors to avoid recomputation of AI model calls.
"""

import asyncio
import hashlib
import logging
import json
import os

from typing import Dict, List, Optional, Any
from datetime import datetime

from core.singleton import SingletonServiceBase
from config.app_constants import AppConstants

logger = logging.getLogger(__name__)

class EmbeddingCacheService(SingletonServiceBase):
    """Service for caching and managing embedding vectors to optimize AI model performance"""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the embedding cache service."""

        self.cache_file_path = AppConstants.EMBEDDINGS_CACHE_FILEPATH
        self._cache_data: Dict[str, Any] = {}
        self._cache_loaded = False
        self._cache_lock = asyncio.Lock()

        self._log_initialization("Embedding cache service initialized successfully", logger)

    async def initialize(self):
        """Initialize the embedding cache and load existing data."""

        try:
            await self._load_cache()
            logger.info("Embedding cache service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize embedding cache service: {e}")
            raise

    async def _load_cache(self):
        """Load existing cache data from file."""

        async with self._cache_lock:
            try:
                if os.path.exists(self.cache_file_path):
                    with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                        self._cache_data = json.load(f)

                    embeddings_count = len(self._cache_data.get('embeddings', {}))
                    logger.info(f"Loaded {embeddings_count} cached embeddings from {self.cache_file_path}")

                else:
                    self._cache_data = {
                        'metadata': {
                            'created_at': datetime.now().isoformat(),
                            'total_embeddings': 0
                        },
                        'embeddings': {}
                    }

                    os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
                    logger.info(f"Initialized empty embedding cache at {self.cache_file_path}")

                self._cache_loaded = True

            except Exception as e:
                logger.error(f"Failed to load embedding cache: {e}")

                self._cache_data = {
                    'metadata': {'total_embeddings': 0},
                    'embeddings': {}
                }

                self._cache_loaded = True

    async def _save_cache(self):
        """Save cache data to file."""

        try:
            self._cache_data['metadata']['updated_at'] = datetime.now().isoformat()
            self._cache_data['metadata']['total_embeddings'] = len(self._cache_data['embeddings'])

            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            temp_file = f"{self.cache_file_path}.tmp"

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_data, f, indent=2, ensure_ascii=False)

            os.replace(temp_file, self.cache_file_path)
            logger.debug(f"Saved embedding cache with {len(self._cache_data['embeddings'])} entries")

        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")
            temp_file = f"{self.cache_file_path}.tmp"

            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)

                except:
                    pass

    def _generate_cache_key(self, text: str, model_name: Optional[str] = None) -> str:
        """Generate a consistent cache key for text and model combination."""

        normalized_text = text.lower().strip()
        cache_input = f"{normalized_text}:{model_name or 'default'}"

        return hashlib.sha256(cache_input.encode('utf-8')).hexdigest()

    async def get_cached_embedding(self, text: str, model_name: Optional[str] = None) -> Optional[List[float]]:
        """Get cached embedding for text if it exists."""

        if not self._cache_loaded:
            await self._load_cache()

        cache_key = self._generate_cache_key(text, model_name)

        async with self._cache_lock:
            cache_entry = self._cache_data['embeddings'].get(cache_key)

            if cache_entry:
                logger.debug(f"Cache hit for text: '{text[:50]}...'")
                return cache_entry['embedding']

            logger.debug(f"Cache miss for text: '{text[:50]}...'")
            return None

    async def store_embedding(self, text: str, embedding: List[float], model_name: Optional[str] = None):
        """Store embedding in cache."""

        if not self._cache_loaded:
            await self._load_cache()

        cache_key = self._generate_cache_key(text, model_name)

        async with self._cache_lock:
            self._cache_data['embeddings'][cache_key] = {
                'text': text,
                'embedding': embedding,
                'model': model_name or 'default',
                'cached_at': datetime.now().isoformat()
            }

            await self._save_cache()
            logger.debug(f"Cached embedding for text: '{text[:50]}...'")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""

        if not self._cache_loaded:
            await self._load_cache()

        async with self._cache_lock:
            embeddings = self._cache_data.get('embeddings', {})

            return {
                'total_embeddings': len(embeddings),
                'cache_file_size_bytes': os.path.getsize(self.cache_file_path) if os.path.exists(self.cache_file_path) else 0,
                'metadata': self._cache_data.get('metadata', {}),
                'models_cached': list(set(entry.get('model', 'default') for entry in embeddings.values()))
            }

    async def clear_cache(self):
        """Clear all cached embeddings."""

        async with self._cache_lock:
            self._cache_data = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total_embeddings': 0
                },
                'embeddings': {}
            }

            await self._save_cache()
            logger.info("Embedding cache cleared")

embedding_cache_service = EmbeddingCacheService()
