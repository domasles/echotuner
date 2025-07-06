"""
AI Model Configuration for EchoTuner API.
Supports multiple AI model endpoints including Ollama and custom models.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel

from config.settings import settings

class AIModelConfig(BaseModel):
    """Configuration for AI model endpoints."""
    
    name: str
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    generation_model: str
    embedding_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class AIModelManager:
    """Manager for AI model configurations."""

    def __init__(self):
        self._models: Dict[str, AIModelConfig] = {}
        self._provider: str = "ollama"

        self._setup_default_models()
    
    def _setup_default_models(self):
        """Setup default model configurations."""

        self._models["ollama"] = AIModelConfig(
            name="Ollama",
            endpoint=settings.AI_ENDPOINT,
            generation_model=settings.AI_GENERATION_MODEL,
            embedding_model=settings.AI_EMBEDDING_MODEL,
            timeout=settings.AI_TIMEOUT
        )

        if settings.CLOUD_API_KEY:
            self._models["openai"] = AIModelConfig(
                name="OpenAI",
                endpoint=settings.AI_ENDPOINT,
                generation_model=settings.AI_GENERATION_MODEL,
                embedding_model=settings.AI_EMBEDDING_MODEL,
                headers={"Authorization": f"Bearer {settings.CLOUD_API_KEY}"},
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

            self._models["anthropic"] = AIModelConfig(
                name="Anthropic",
                endpoint=settings.AI_ENDPOINT,
                generation_model=settings.AI_GENERATION_MODEL,
                embedding_model=None,  # Anthropic doesn't provide embeddings
                headers={
                    "x-api-key": settings.CLOUD_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

            self._models["google"] = AIModelConfig(
                name="Google",
                endpoint=settings.AI_ENDPOINT,
                generation_model=settings.AI_GENERATION_MODEL,
                embedding_model=settings.AI_EMBEDDING_MODEL,
                headers={"x-goog-api-key": settings.CLOUD_API_KEY},
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

        self._provider = settings.AI_PROVIDER

    def register_model(self, model_id: str, config: AIModelConfig):
        """Register a new AI model configuration."""

        self._models[model_id] = config

    def get_provider(self, model_id: Optional[str] = None) -> AIModelConfig:
        """Get model configuration by ID."""

        if model_id is None:
            model_id = self._provider

        if model_id not in self._models:
            raise ValueError(f"Unknown model: {model_id}")

        return self._models[model_id]

    def list_models(self) -> List[str]:
        """List available model IDs."""

        return list(self._models.keys())

ai_model_manager = AIModelManager()
