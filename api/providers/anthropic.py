"""
Anthropic AI Provider for EchoTuner API.

This module implements the Anthropic provider for Claude models.
"""

import logging
from typing import List

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseAIProvider):
    """Anthropic AI provider implementation."""
    
    @property
    def name(self) -> str:
        return "Anthropic"
    
    @property
    def supports_embeddings(self) -> bool:
        return False  # Anthropic doesn't provide embeddings
    
    async def test_availability(self) -> bool:
        """Test if Anthropic is available."""
        try:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"

            test_payload = {
                "model": self.generation_model,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Hello"}]
            }

            async with self._session.post(
                f"{self.endpoint}/v1/messages",
                headers=headers,
                json=test_payload,
                timeout=10
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.debug(f"Anthropic availability test failed: {e}")
            return False
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Anthropic Claude."""
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": self.generation_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }

        async with self._session.post(
            f"{self.endpoint}/v1/messages",
            headers=headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic request failed: {error_text}")

            result = await response.json()
            return result["content"][0]["text"]
    
    async def _get_embedding_impl(self, text: str, **kwargs) -> List[float]:
        """Anthropic does not support embeddings."""
        raise NotImplementedError("Anthropic does not provide embedding models")
