import numpy as np
import requests
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class PromptValidatorService:
    """
    Lightweight model to validate if user input is music/mood related.
    Uses Ollama with thenlper/gte-small for embedding-based validation.
    """
    
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_VALIDATION_MODEL
        self.use_ollama = settings.USE_OLLAMA

        self.prompt_validation_threshold = settings.PROMPT_VALIDATION_THRESHOLD
        self.prompt_validation_timeout = settings.PROMPT_VALIDATION_TIMEOUT

        self.music_reference_embeddings = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the model asynchronously"""

        try:
            logger.info("Initializing mood validation with Ollama...")
            
            if not self.use_ollama:
                logger.error("Ollama is required for this application")
                raise RuntimeError("Ollama must be enabled. Set USE_OLLAMA=true in environment variables.")

            if not await self._check_ollama_connection():
                logger.error("Ollama not running or not accessible")
                raise RuntimeError("Ollama is not running. Please start Ollama and try again.")
            
            await self._ensure_model_available()
            await self._compute_reference_embeddings()
            
            self.initialized = True
            logger.info("Mood validation with Ollama initialized successfully!")
            
        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Prompt validator initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize prompt validator: {e}")
    
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
        """Ensure the model is available in Ollama"""

        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name not in model_names:
                    logger.info(f"Pulling model {self.model_name}...")

                    pull_response = requests.post(
                        f"{self.ollama_base_url}/api/pull",
                        json={"name": self.model_name}
                    )

                    if pull_response.status_code == 200:
                        logger.info(f"Model {self.model_name} pulled successfully")

                    else:
                        logger.error(f"Failed to pull model: {pull_response.text}")
                        raise RuntimeError(f"Failed to pull model {self.model_name}")
                    
                else:
                    logger.info(f"Model {self.model_name} already available")

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
            music_references = [
                "I want to listen to music",
                "I'm feeling happy and want upbeat songs",
                "I need relaxing music",
                "Play some energetic music",
                "I'm sad and want emotional songs",
                "I want to hear my favorite artist",
                "Put on some background music",
                "I need workout music",
                "Play romantic songs",
                "I want to discover new music"
            ]
            
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
        """Get embedding for text using Ollama"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=self.prompt_validation_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return np.array(result.get('embedding', []))
            
            else:
                logger.error(f"Failed to get embedding: {response.text}")
                raise RuntimeError(f"Failed to get embedding from Ollama")
                
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

                logger.debug(f"Semantic similarity: {max_similarity:.3f}, threshold: {self.prompt_validation_threshold}, valid: {is_similar}")
                return is_similar
                    
            except RuntimeError:
                raise

            except Exception as e:
                logger.error(f"Prompt validation failed: {e}")
                raise RuntimeError(f"Prompt validation failed: {e}")
            
        else:
            logger.error("Reference embeddings not available")
            raise RuntimeError("Reference embeddings not available for validation")

