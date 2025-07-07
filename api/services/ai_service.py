"""
AI service.
Handles AI model interactions using the modular provider system.
"""

import logging
from typing import Dict, Any, Optional, List

from core.singleton import SingletonServiceBase
from providers.registry import provider_registry
from providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

class AIService(SingletonServiceBase):
    """Service for interacting with AI models using the provider system."""
    
    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the AIService."""
        self._current_provider: Optional[BaseAIProvider] = None
        self._log_initialization("AI service initialized successfully", logger)
    
    async def initialize(self):
        """Initialize the AI service."""
        # Prevent multiple initializations
        if self._current_provider and getattr(self._current_provider, '_session', None):
            logger.debug("AI service already initialized, skipping")
            return
            
        try:
            logger.debug("Initializing AI service...")
            self._current_provider = provider_registry.get_provider()
            await self._current_provider.initialize()
            
            logger.info(f"AI Service initialized with {self._current_provider.name}")

        except Exception as e:
            logger.error(f"AI service initialization failed: {e}")
            raise

    async def close(self):
        """Close the AI service and cleanup resources."""
        if self._current_provider:
            await self._current_provider.close()
            self._current_provider = None

    async def generate_text(self, prompt: str, provider_id: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using the specified AI provider.
        
        Args:
            prompt: Input prompt for text generation
            provider_id: Optional provider ID (uses default if None)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        try:
            if provider_id and provider_id != getattr(self._current_provider, 'name', '').lower():
                # Different provider requested, create new instance
                provider = provider_registry.get_provider(provider_id)
                await provider.initialize()
            else:
                # Use current provider
                provider = self._current_provider
                
            if not provider:
                raise Exception("No AI provider available")
            
            return await provider.generate_text(prompt, **kwargs)

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise Exception(f"Text generation failed: {e}")

    async def get_embedding(self, text: str, provider_id: Optional[str] = None, **kwargs) -> List[float]:
        """
        Get text embedding using the specified provider.
        
        Args:
            text: Input text for embedding
            provider_id: Optional provider ID (uses default if None)
            **kwargs: Additional embedding parameters
            
        Returns:
            Embedding vector
        """
        try:
            if provider_id and provider_id != getattr(self._current_provider, 'name', '').lower():
                # Different provider requested, create new instance
                provider = provider_registry.get_provider(provider_id)
                await provider.initialize()
            else:
                # Use current provider
                provider = self._current_provider
                
            if not provider:
                raise Exception("No AI provider available")
            
            return await provider.get_embedding(text, **kwargs)

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise Exception(f"Embedding generation failed: {e}")

    def list_available_providers(self) -> List[str]:
        """List all available AI providers."""
        return provider_registry.list_providers()

    def get_provider_info(self, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific provider."""
        provider = provider_registry.get_provider(provider_id)
        return provider.get_info()

    # Legacy compatibility methods for smooth transition
    
    async def _test_model_availability(self, model_config) -> bool:
        """Legacy method for backward compatibility."""
        try:
            if self._current_provider:
                return await self._current_provider.test_availability()
            return False
        except Exception:
            return False

    def list_available_models(self) -> List[str]:
        """Legacy method - use list_available_providers instead."""
        return self.list_available_providers()

    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method - use get_provider_info instead."""
        return self.get_provider_info(model_id)

ai_service = AIService()
