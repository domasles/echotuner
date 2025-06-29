import numpy as np
import logging
import httpx

from services.data_loader import data_loader
from config.settings import settings
from config.ai_models import ai_model_manager

logger = logging.getLogger(__name__)

class PromptValidatorService:
    """Lightweight model to validate if user input is music/mood related."""

    def __init__(self):
        self.model_config = ai_model_manager.get_model()
        
        self.prompt_validation_threshold = settings.PROMPT_VALIDATION_THRESHOLD
        self.prompt_validation_timeout = settings.PROMPT_VALIDATION_TIMEOUT

        self.music_reference_embeddings = None
        self.initialized = False
        self.http_client = None

    async def initialize(self):
        """Initialize the model asynchronously"""

        try:
            self.http_client = httpx.AsyncClient(timeout=self.model_config.timeout)

            if not await self._check_ai_model_connection():
                logger.error("AI model not running or not accessible")
                raise RuntimeError("AI model is not running. Please check your AI model configuration and try again.")

            await self._ensure_model_available()
            await self._compute_reference_embeddings()

            logger.info("Prompt validator initialized successfully!")
            self.initialized = True

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Prompt validator initialization failed: {e}")
            raise RuntimeError(f"Prompt validator initialization failed: {e}")

    def is_ready(self) -> bool:
        """Check if the service is ready"""

        return self.initialized

    async def _check_ai_model_connection(self) -> bool:
        """Check if AI model is running and accessible"""

        try:
            response = await self.http_client.get(f"{self.model_config.endpoint}/api/tags")
            return response.status_code == 200

        except:
            return False

    async def _ensure_model_available(self):
        """Ensure the model is available"""

        try:
            # Only check for Ollama models that need to be pulled
            if self.model_config.name.lower() != "ollama":
                logger.info(f"Using external AI model: {self.model_config.name}")
                return
                
            response = await self.http_client.get(f"{self.model_config.endpoint}/api/tags")

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]

                if self.model_config.embedding_model and self.model_config.embedding_model not in model_names:
                    logger.info(f"Pulling embedding model {self.model_config.embedding_model}...")

                    pull_response = await self.http_client.post(
                        f"{self.model_config.endpoint}/api/pull",
                        json={"name": self.model_config.embedding_model}
                    )

                    if pull_response.status_code == 200:
                        logger.info(f"Embedding model {self.model_config.embedding_model} pulled successfully")
                    else:
                        logger.error(f"Failed to pull embedding model: {pull_response.text}")
                        raise RuntimeError(f"Failed to pull embedding model {self.model_config.embedding_model}")

                elif self.model_config.model_name not in model_names:
                    logger.info(f"Pulling model {self.model_config.model_name}...")

                    pull_response = await self.http_client.post(
                        f"{self.model_config.endpoint}/api/pull",
                        json={"name": self.model_config.model_name}
                    )

                    if pull_response.status_code == 200:
                        logger.info(f"Model {self.model_config.model_name} pulled successfully")

                    else:
                        logger.error(f"Failed to pull model: {pull_response.text}")
                        raise RuntimeError(f"Failed to pull model {self.model_config.model_name}")

                else:
                    logger.info(f"Model {self.model_config.model_name} already available")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Model availability check failed: {e}")
            raise RuntimeError(f"Model availability check failed: {e}")

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """Normalize a vector to unit length"""

        norm = np.linalg.norm(vector)
        return vector / norm if norm else np.zeros_like(vector)

    async def _compute_reference_embeddings(self):
        """Pre-compute embeddings for music-related reference texts"""

        try:
            music_references = data_loader.get_prompt_references()
            embeddings = []

            for text in music_references:
                embedding = await self._get_embedding(text)

                if embedding is not None:
                    embedding = self._normalize(embedding)
                    embeddings.append(embedding)

            if embeddings:
                self.music_reference_embeddings = np.array(embeddings)
                logger.info(f"Computed {len(embeddings)} reference embeddings")

            else:
                logger.error("No reference embeddings computed")
                raise RuntimeError("Failed to compute reference embeddings")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Reference embeddings computation failed: {e}")
            raise RuntimeError(f"Failed to compute reference embeddings: {e}")

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using AI model"""

        try:
            response = await self.http_client.post(
                f"{self.model_config.endpoint}/api/embeddings",
                json={
                    "model": self.model_config.embedding_model or self.model_config.model_name,
                    "prompt": text
                },
                timeout=self.prompt_validation_timeout
            )

            if response.status_code == 200:
                result = response.json()
                return np.array(result.get('embedding', []))

            else:
                logger.error(f"Failed to get embedding: {response.text}")
                raise RuntimeError(f"Failed to get embedding from AI model")

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            raise RuntimeError(f"Embedding request failed: {e}")

    async def validate_prompt(self, prompt: str) -> bool:
        """
        Validate if the prompt is related to music, mood, or emotions.
        Returns True if valid, False otherwise.
        """

        if not self.initialized:
            await self.initialize()

        prompt = prompt.lower().strip()

        if len(prompt) < 3 or len(prompt) > 500:
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

                logger.info(f"Semantic similarity: {max_similarity:.3f}, threshold: {self.prompt_validation_threshold}, valid: {is_similar}")

                return is_similar

            except RuntimeError:
                raise

            except Exception as e:
                logger.error(f"Prompt validation failed: {e}")
                raise RuntimeError(f"Prompt validation failed: {e}")

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
