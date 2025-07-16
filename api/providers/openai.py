"""
OpenAI AI Provider for EchoTuner API.

This module implements the OpenAI provider for cloud AI models.
"""

import logging

from typing import List

from .base import BaseAIProvider
from core.service.session_decorators import ensure_session_initialized

from config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI AI provider implementation."""
    
    def __init__(self):
        """Initialize OpenAI provider."""

        super().__init__()
        
        self.name = "openai"
        self.headers = {"Authorization": f"Bearer {settings.CLOUD_API_KEY}"}

    @ensure_session_initialized
    async def test_availability(self) -> bool:
        """Test if OpenAI is available."""

        try:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"

            test_payload = {
                "model": self.generation_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }

            async with self._session.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            ) as response:
                return response.status == 200

        except Exception as e:
            logger.debug(f"OpenAI availability test failed: {e}")
            return False

    @ensure_session_initialized
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI."""

        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": self.generation_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }

        async with self._session.post(
            f"{self.endpoint}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI request failed: {error_text}")

            result = await response.json()
            return result["choices"][0]["message"]["content"]

    @ensure_session_initialized
    async def get_embedding(self, text: str, **kwargs) -> List[float]:
        """Get embedding using OpenAI."""

        if not self.embedding_model:
            raise Exception("No embedding model configured for OpenAI")

        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": self.embedding_model,
            "input": text
        }

        async with self._session.post(
            f"{self.endpoint}/v1/embeddings",
            headers=headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI embedding request failed: {error_text}")

            result = await response.json()
            return result["data"][0]["embedding"]
