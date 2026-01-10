"""
AI Provider Registry for EchoTuner API.

This module handles registration and creation of AI providers.
"""

import importlib
import logging
import inspect

from typing import Dict, Type, Optional, List, Any
from pathlib import Path

from infrastructure.singleton import SingletonServiceBase
from domain.config.settings import settings

from .custom_template import CustomProvider, AdvancedCustomProvider
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class ProviderRegistry(SingletonServiceBase):
    """Registry for AI providers with service capabilities."""

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the provider registry."""
        self._providers: Dict[str, Type[BaseAIProvider]] = {}
        self._provider_instances: Dict[str, BaseAIProvider] = {}
        self._current_provider: str = ""
        self._active_provider_instance: Optional[BaseAIProvider] = None

        self._auto_register_providers()
        self._setup_default_providers()

        # Initialize the current provider
        if self._current_provider:
            try:
                self._active_provider_instance = self.get_provider()
                await self._active_provider_instance.initialize()
                logger.info(f"AI Provider Registry initialized with {self._active_provider_instance.name}")
            except Exception as e:
                logger.error(f"AI provider initialization failed: {e}")
                raise RuntimeError(f"AI provider initialization failed: {e}")

    async def cleanup(self):
        """Async cleanup of all providers."""
        if self._active_provider_instance:
            await self._active_provider_instance.close()
            self._active_provider_instance = None

        await self.close_all()
        logger.info("AI provider registry cleaned up")

    def _auto_register_providers(self):
        """Automatically discover and register all provider classes."""

        providers_dir = Path(__file__).parent

        for file_path in providers_dir.glob("*.py"):
            if file_path.name in ["__init__.py", "base.py", "registry.py"]:
                continue

            module_name = file_path.stem

            try:
                module = importlib.import_module(f"infrastructure.ai.{module_name}")

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseAIProvider) and obj not in (
                        BaseAIProvider,
                        CustomProvider,
                        AdvancedCustomProvider,
                    ):
                        provider = obj()
                        provider_name = provider.get_info().get("name", "").lower()

                        self.register(provider_name, obj)
                        logger.debug(f"Auto-registered provider: {provider_name}")

            except Exception as e:
                logger.warning(f"Failed to auto-register providers from {module_name}: {e}")

    def _setup_default_providers(self):
        """Setup default provider instances with configurations from settings."""

        for provider_name, provider_class in self._providers.items():
            try:
                self._provider_instances[provider_name] = provider_class()
                logger.debug(f"Created default instance for provider: {provider_name}")

            except Exception as e:
                logger.warning(f"Failed to create default instance for {provider_name}: {e}")

        self._current_provider = settings.AI_PROVIDER

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

    def register_provider_instance(self, provider_id: str, provider: BaseAIProvider):
        """Register a provider instance."""

        self._provider_instances[provider_id] = provider

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

    def get_provider(self, provider_id: Optional[str] = None) -> BaseAIProvider:
        """Get provider instance by ID."""

        if provider_id is None:
            provider_id = self._current_provider

        if provider_id not in self._provider_instances:
            raise ValueError(f"Unknown provider: {provider_id}")

        return self._provider_instances[provider_id]

    def list_providers(self) -> List[str]:
        """List all registered provider names."""

        return list(self._provider_instances.keys())

    def get_provider_class(self, name: str) -> Optional[Type[BaseAIProvider]]:
        """Get provider class by name."""

        return self._providers.get(name.lower())

    async def close_all(self):
        """Close all provider instances."""

        for provider_id, provider in self._provider_instances.items():
            try:
                await provider.close()
                logger.debug(f"Closed provider: {provider_id}")
            except Exception as e:
                logger.warning(f"Error closing provider {provider_id}: {e}")

        self._provider_instances.clear()

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
        from domain.shared.validation.validators import UniversalValidator

        try:
            if not self._active_provider_instance:
                self._active_provider_instance = self.get_provider(provider_id)
                await self._active_provider_instance.initialize()

            return await self._active_provider_instance.generate_text(prompt, **kwargs)

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            logger.error("Full traceback:", exc_info=True)
            raise Exception(f"Text generation failed: {str(e)}")

    def get_provider_info(self, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific provider."""
        provider = self.get_provider(provider_id)
        return provider.get_info()


provider_registry = ProviderRegistry()
