"""
Ollama AI Provider for EchoTuner API.

This module implements the Ollama provider for local AI models.
"""

import logging

from typing import List

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Ollama AI provider implementation."""

    def __init__(self):
        """Initialize Ollama provider."""

        super().__init__()
        self.name = "ollama"

    async def test_availability(self) -> bool:
        """Test if Ollama is available."""

        try:
            response = await self._client.get(f"{self.endpoint}/api/tags")
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Ollama availability test failed: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""

        payload = {
            "model": self.generation_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        response = await self._client.post(f"{self.endpoint}/api/generate", json=payload, timeout=self.timeout)

        if response.status_code != 200:
            raise Exception(f"Ollama request failed: {response.text}")

        result = response.json()
        return result.get("response", "")
