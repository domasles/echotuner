"""
AI Provider Manager for EchoTuner API.
Manages AI provider selection and orchestration.
"""

import logging
from typing import Optional, Dict, Any

from core.singleton import SingletonServiceBase
from core.service.decorators import service_optional_operation

from providers.registry import provider_registry

logger = logging.getLogger(__name__)

class ProviderManager(SingletonServiceBase):
    """Service for managing AI provider selection and orchestration."""

    def __init__(self):
        super().__init__()
    
    def _setup_service(self):
        """Initialize the ProviderManager."""
        self.provider_registry = provider_registry
        self._log_initialization("Provider manager initialized successfully", logger)

    @service_optional_operation("get_active_provider")
    async def get_active_provider(self) -> Optional[Any]:
        """Get the currently active AI provider."""
        try:
            return await self.provider_registry.get_active_provider()
        except Exception as e:
            logger.error(f"Failed to get active provider: {e}")
            return None

    @service_optional_operation("set_active_provider")
    async def set_active_provider(self, provider_name: str) -> bool:
        """Set the active AI provider."""
        try:
            return await self.provider_registry.set_active_provider(provider_name)
        except Exception as e:
            logger.error(f"Failed to set active provider: {e}")
            return False

    @service_optional_operation("get_provider_info")
    async def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific provider."""
        try:
            provider = await self.provider_registry.get_provider(provider_name)
            if not provider:
                return None
            
            return {
                "name": provider.name,
                "is_available": provider.is_available(),
                "capabilities": provider.get_capabilities(),
                "status": provider.get_status()
            }
        except Exception as e:
            logger.error(f"Failed to get provider info: {e}")
            return None

    @service_optional_operation("list_providers")
    async def list_providers(self) -> Optional[Dict[str, Any]]:
        """List all available providers."""
        try:
            providers = await self.provider_registry.list_providers()
            return {
                "providers": [
                    {
                        "name": p.name,
                        "is_available": p.is_available(),
                        "is_active": p == await self.provider_registry.get_active_provider()
                    }
                    for p in providers
                ]
            }
        except Exception as e:
            logger.error(f"Failed to list providers: {e}")
            return None

provider_manager = ProviderManager()
