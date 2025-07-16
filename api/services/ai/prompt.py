"""
Prompt validator service.
Validates if user input is related to music, mood, or emotions.
"""

import numpy as np
import asyncio
import logging
import httpx

from core.singleton import SingletonServiceBase

from providers.registry import provider_registry
from config.settings import settings

from services.ai.embedding_cache import embedding_cache_service
from services.data.data import data_loader
from services.ai.ai import ai_service

from core.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class PromptValidatorService(SingletonServiceBase):
    """Lightweight model to validate if user input is music/mood related."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the PromptValidatorService."""

        self.model_config = provider_registry.get_provider()
        self.prompt_validation_threshold = settings.PROMPT_VALIDATION_THRESHOLD
        self.prompt_validation_timeout = settings.PROMPT_VALIDATION_TIMEOUT

        self.music_reference_embeddings = None
        self.http_client = None

        self._log_initialization("Prompt validator service initialized successfully", logger)

    async def initialize(self):
        """Initialize the model asynchronously"""

        try:
            self.http_client = httpx.AsyncClient(timeout=self.model_config.timeout)

            if not await ai_service._current_provider.test_availability():
                logger.error("AI model not running or not accessible")
                raise RuntimeError("AI model is not running. Please check your AI model configuration and try again.")

            asyncio.create_task(self._compute_reference_embeddings_async())

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Prompt validator initialization failed: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Prompt validator initialization failed: {sanitized_error}")

    async def _compute_reference_embeddings_async(self):
        """Compute reference embeddings asynchronously without blocking startup"""

        try:
            logger.info("Computing reference embeddings in background...")
            await self._compute_reference_embeddings()
            logger.info("Reference embeddings computed successfully")

        except Exception as e:
            logger.error(f"Failed to compute reference embeddings: {e}")

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """Normalize a vector to unit length"""

        norm = np.linalg.norm(vector)
        return vector / norm if norm else np.zeros_like(vector)

    async def _compute_reference_embeddings(self):
        """Pre-compute embeddings for music-related reference texts with concurrency"""

        try:
            music_references = data_loader.get_prompt_references()
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

            async def get_embedding_with_semaphore(text):
                async with semaphore:
                    try:
                        embedding = await self._get_embedding(text)

                        if embedding is not None:
                            return self._normalize(embedding)

                    except Exception as e:
                        logger.debug(f"Failed to get embedding for '{text[:30]}...': {e}")

                    return None

            tasks = [get_embedding_with_semaphore(text) for text in music_references]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            embeddings = [result for result in results if result is not None and not isinstance(result, Exception)]

            if embeddings:
                self.music_reference_embeddings = np.array(embeddings)
                logger.info(f"Computed {len(embeddings)} reference embeddings")

            else:
                logger.error("No reference embeddings computed")
                raise RuntimeError("Failed to compute reference embeddings")

        except Exception as e:
            logger.error(f"Reference embeddings computation failed: {e}")
            raise RuntimeError(f"Failed to compute reference embeddings: {e}")

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using AI model with caching"""

        try:
            cached_embedding = await embedding_cache_service.get_cached_embedding(text, self.model_config.embedding_model)

            if cached_embedding is not None:
                return np.array(cached_embedding)

            embedding = await ai_service.get_embedding(text, model_id=None)
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)

            await embedding_cache_service.store_embedding(text, embedding_list, self.model_config.embedding_model)
            return np.array(embedding)

        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            raise RuntimeError(f"Embedding request failed: {e}")

    async def validate_prompt(self, prompt: str) -> bool:
        """
        Validate if the prompt is related to music, mood, or emotions.
        Returns True if valid, False otherwise.
        """

        prompt = prompt.lower().strip()

        if len(prompt) < 3 or len(prompt) > settings.MAX_PROMPT_LENGTH:
            return False

        if self.music_reference_embeddings is not None:
            try:
                prompt_embedding = await self._get_embedding(prompt)

                if prompt_embedding is None or len(prompt_embedding) == 0:
                    logger.error("Failed to get prompt embedding")
                    raise RuntimeError("Failed to get prompt embedding")

                prompt_embedding = self._normalize(prompt_embedding)
                similarities = np.dot(self.music_reference_embeddings, prompt_embedding)
                max_similarity = np.max(similarities)
                is_similar = max_similarity > self.prompt_validation_threshold
                logger.debug(f"Semantic similarity: {max_similarity:.3f}, threshold: {self.prompt_validation_threshold}, valid: {is_similar}")

                return is_similar

            except RuntimeError:
                raise

            except Exception as e:
                logger.error(f"Prompt validation failed: {e}")
                sanitized_error = UniversalValidator.sanitize_error_message(str(e))

                raise RuntimeError(f"Prompt validation failed: {sanitized_error}")

        else:
            logger.error("Reference embeddings not available")
            raise RuntimeError("Reference embeddings not available for validation")

    async def __aenter__(self):
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=self.model_config.timeout)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    def __del__(self):
        """Cleanup HTTP client on destruction"""

        try:
            if self.http_client and not self.http_client.is_closed:
                import asyncio

                try:
                    loop = asyncio.get_event_loop()

                    if loop.is_running():
                        loop.create_task(self.http_client.aclose())

                    else:
                        loop.run_until_complete(self.http_client.aclose())

                except:
                    pass

        except:
            pass

prompt_validator_service = PromptValidatorService()
