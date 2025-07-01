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
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    model_name: str
    embedding_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class AIModelManager:
    """Manager for AI model configurations."""

    def __init__(self):
        self._models: Dict[str, AIModelConfig] = {}
        self._default_provider: str = "ollama"
        self._setup_default_models()
    
    def _setup_default_models(self):
        """Setup default model configurations."""

        self._models["ollama"] = AIModelConfig(
            name="Ollama",
            endpoint=settings.AI_ENDPOINT,
            model_name=settings.AI_GENERATION_MODEL,
            embedding_model=settings.AI_EMBEDDING_MODEL,
            timeout=settings.AI_TIMEOUT
        )

        if settings.OPENAI_API_KEY:
            self._models["openai"] = AIModelConfig(
                name="OpenAI",
                endpoint="https://api.openai.com/v1",
                api_key=settings.OPENAI_API_KEY,
                model_name="gpt-4o-mini",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                max_tokens=2000,
                temperature=0.7
            )

        if settings.ANTHROPIC_API_KEY:
            self._models["anthropic"] = AIModelConfig(
                name="Anthropic",
                endpoint="https://api.anthropic.com/v1",
                api_key=settings.ANTHROPIC_API_KEY,
                model_name="claude-3-5-sonnet-20241022",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                max_tokens=2000,
                temperature=0.7
            )

        if hasattr(settings, 'DEFAULT_AI_PROVIDER') and settings.DEFAULT_AI_PROVIDER in self._models:
            self._default_provider = settings.DEFAULT_AI_PROVIDER

    def register_model(self, model_id: str, config: AIModelConfig):
        """Register a new AI model configuration."""
        self._models[model_id] = config

    def get_provider(self, model_id: Optional[str] = None) -> AIModelConfig:
        """Get model configuration by ID."""

        if model_id is None:
            model_id = self._default_provider

        if model_id not in self._models:
            raise ValueError(f"Unknown model: {model_id}")

        return self._models[model_id]

    def list_models(self) -> List[str]:
        """List available model IDs."""

        return list(self._models.keys())

    def set_default_model(self, model_id: str):
        """Set the default model."""

        if model_id not in self._models:
            raise ValueError(f"Unknown model: {model_id}")

        self._default_provider = model_id
    
    def get_default_model(self) -> str:
        """Get the default model ID."""

        return self._default_provider

ai_model_manager = AIModelManager()
