"""
Base AI Provider for EchoTuner API.

This module defines the base interface that all AI providers must implement.
"""

import httpx
import asyncio
import logging

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from domain.config.settings import settings

logger = logging.getLogger(__name__)

# Shared global httpx client for all AI providers (connection pooling)
_shared_ai_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()  # Prevent race condition on client creation

class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self):
        """Initialize the AI provider with settings."""

        self.name = ""
        self.endpoint = settings.AI_ENDPOINT
        self.headers = {}
        self.generation_model = settings.AI_GENERATION_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize the provider (uses shared client for connection pooling)."""
        global _shared_ai_client
        
        async with _client_lock:  # Prevent race condition
            if _shared_ai_client is None:
                # Create shared client with connection pooling (100 max connections)
                _shared_ai_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    limits=httpx.Limits(
                        max_connections=100,
                        max_keepalive_connections=20
                    )
                )
                logger.debug("Created shared httpx client for AI providers")
        
        # All providers use the shared client
        self._client = _shared_ai_client

    @abstractmethod
    async def test_availability(self) -> bool:
        """Test if the provider is available and responding."""

        pass

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using this provider.

        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """

        pass

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""

        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "generation_model": self.generation_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }

async def cleanup_shared_ai_client():
    """Cleanup the shared httpx client on application shutdown."""
    global _shared_ai_client
    
    if _shared_ai_client:
        await _shared_ai_client.aclose()
        _shared_ai_client = None
        logger.debug("Closed shared httpx client for AI providers")
