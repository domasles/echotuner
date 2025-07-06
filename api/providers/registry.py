"""
AI Provider Registry for EchoTuner API.

This module handles registration and creation of AI providers.
"""

import logging
from typing import Dict, Type, Optional, List

from .base import BaseAIProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """Registry for AI providers."""
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseAIProvider]] = {}
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register built-in providers."""
        self.register("ollama", OllamaProvider)
        self.register("openai", OpenAIProvider)
        self.register("anthropic", AnthropicProvider)
        self.register("google", GoogleProvider)
    
    def register(self, name: str, provider_class: Type[BaseAIProvider]):
        """
        Register a provider class.
        
        Args:
            name: Provider name (lowercase)
            provider_class: Provider class that inherits from BaseAIProvider
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError(f"Provider class must inherit from BaseAIProvider")
        
        self._providers[name.lower()] = provider_class
        logger.debug(f"Registered AI provider: {name}")
    
    def create_provider(self, name: str, **kwargs) -> BaseAIProvider:
        """
        Create a provider instance.
        
        Args:
            name: Provider name
            **kwargs: Provider configuration parameters
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider is not registered
        """
        provider_class = self._providers.get(name.lower())
        if not provider_class:
            available = list(self._providers.keys())
            raise ValueError(f"Unknown provider '{name}'. Available: {available}")
        
        return provider_class(**kwargs)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    def get_provider_class(self, name: str) -> Optional[Type[BaseAIProvider]]:
        """Get provider class by name."""
        return self._providers.get(name.lower())

# Global registry instance
provider_registry = ProviderRegistry()

def register_custom_provider(name: str, provider_class: Type[BaseAIProvider]):
    """
    Convenience function to register a custom provider.
    
    Example:
        from providers.registry import register_custom_provider
        from my_custom_provider import MyProvider
        
        register_custom_provider("my_provider", MyProvider)
    """
    provider_registry.register(name, provider_class)
