"""
AI Model Configuration for EchoTuner API.
Supports multiple AI model endpoints including Ollama and custom models.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel

from config.settings import settings
from providers.registry import provider_registry, BaseAIProvider

class AIModelConfig(BaseModel):
    """Configuration for AI model endpoints (legacy compatibility)."""
    
    name: str
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    generation_model: str
    embedding_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class AIModelManager:
    """Manager for AI model configurations using the new provider system."""

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._current_provider: str = "ollama"
        self._setup_default_providers()
    
    def _setup_default_providers(self):
        """Setup default provider configurations."""

        self._providers["ollama"] = provider_registry.create_provider(
            name="ollama",
            endpoint=settings.AI_ENDPOINT,
            generation_model=settings.AI_GENERATION_MODEL,
            embedding_model=settings.AI_EMBEDDING_MODEL,
            timeout=settings.AI_TIMEOUT
        )

        if settings.CLOUD_API_KEY:
            self._providers["openai"] = provider_registry.create_provider(
                name="openai",
                endpoint=settings.AI_ENDPOINT,
                generation_model=settings.AI_GENERATION_MODEL,
                embedding_model=settings.AI_EMBEDDING_MODEL,
                headers={"Authorization": f"Bearer {settings.CLOUD_API_KEY}"},
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

            self._providers["anthropic"] = provider_registry.create_provider(
                name="anthropic",
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

            self._providers["google"] = provider_registry.create_provider(
                name="google",
                endpoint=settings.AI_ENDPOINT,
                generation_model=settings.AI_GENERATION_MODEL,
                embedding_model=settings.AI_EMBEDDING_MODEL,
                headers={"x-goog-api-key": settings.CLOUD_API_KEY},
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

        self._current_provider = settings.AI_PROVIDER

    def register_provider(self, provider_id: str, provider: BaseAIProvider):
        """Register a new AI provider instance."""
        self._providers[provider_id] = provider

    def get_provider(self, provider_id: Optional[str] = None) -> BaseAIProvider:
        """Get provider instance by ID."""
        if provider_id is None:
            provider_id = self._current_provider

        if provider_id not in self._providers:
            raise ValueError(f"Unknown provider: {provider_id}")

        return self._providers[provider_id]

    def get_provider_legacy(self, provider_id: Optional[str] = None) -> AIModelConfig:
        """Get legacy model configuration for backward compatibility."""
        provider = self.get_provider(provider_id)
        
        return AIModelConfig(
            name=provider.name,
            endpoint=provider.endpoint,
            headers=provider.headers,
            timeout=provider.timeout,
            generation_model=provider.generation_model,
            embedding_model=provider.embedding_model,
            max_tokens=provider.max_tokens,
            temperature=provider.temperature
        )

    def list_providers(self) -> List[str]:
        """List available provider IDs."""
        return list(self._providers.keys())

ai_model_manager = AIModelManager()
