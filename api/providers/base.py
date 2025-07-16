"""
Base AI Provider for EchoTuner API.

This module defines the base interface that all AI providers must implement.
"""

import aiohttp
import logging

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from config.settings import settings
from core.service.session_decorators import ensure_session_initialized

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self):
        """Initialize the AI provider with settings."""

        self.name = ""
        self.endpoint = settings.AI_ENDPOINT
        self.headers = {}
        self.generation_model = settings.AI_GENERATION_MODEL
        self.embedding_model = settings.AI_EMBEDDING_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        self.timeout = settings.AI_TIMEOUT
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the provider (create session, test connectivity, etc.)."""

        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the provider and cleanup resources."""

        if self._session:
            await self._session.close()
            self._session = None

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
    
    @abstractmethod
    async def get_embedding(self, text: str, **kwargs) -> List[float]:
        """
        Get text embedding using this provider.

        Args:
            text: The input text
            **kwargs: Additional embedding parameters

        Returns:
            Embedding vector
        """

        pass

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""

        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "generation_model": self.generation_model,
            "embedding_model": self.embedding_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
