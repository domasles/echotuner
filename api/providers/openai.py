"""
OpenAI AI Provider for EchoTuner API.

This module implements the OpenAI provider for cloud AI models.
"""

import logging
from typing import List

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI AI provider implementation."""
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def supports_embeddings(self) -> bool:
        return bool(self.embedding_model)
    
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
    
    async def _get_embedding_impl(self, text: str, **kwargs) -> List[float]:
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
