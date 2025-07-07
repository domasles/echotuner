"""
Base AI Provider for EchoTuner API.

This module defines the base interface that all AI providers must implement.
"""

import asyncio
import aiohttp
import logging

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None, generation_model: str = "", embedding_model: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None, timeout: int = 30):
        """
        Initialize the AI provider.
        
        Args:
            endpoint: The API endpoint URL
            headers: HTTP headers for authentication
            generation_model: Model name for text generation
            embedding_model: Model name for embeddings (if supported)
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        self.generation_model = generation_model
        self.embedding_model = embedding_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def supports_embeddings(self) -> bool:
        """Return whether this provider supports embeddings."""
        pass
    
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
    
    async def get_embedding(self, text: str, **kwargs) -> List[float]:
        """
        Get text embedding using this provider.
        
        Args:
            text: The input text
            **kwargs: Additional embedding parameters
            
        Returns:
            Embedding vector
            
        Raises:
            NotImplementedError: If provider doesn't support embeddings
        """
        if not self.supports_embeddings:
            raise NotImplementedError(f"{self.name} does not support embeddings")
        
        return await self._get_embedding_impl(text, **kwargs)
    
    @abstractmethod
    async def _get_embedding_impl(self, text: str, **kwargs) -> List[float]:
        """Implementation-specific embedding method."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "generation_model": self.generation_model,
            "embedding_model": self.embedding_model,
            "supports_embeddings": self.supports_embeddings,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
