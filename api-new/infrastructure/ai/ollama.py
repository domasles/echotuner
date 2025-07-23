"""
Ollama AI Provider for EchoTuner API.

This module implements the Ollama provider for local AI models.
"""

import logging

from typing import List

from .base import BaseAIProvider
from application.core.service.session_decorators import ensure_session_initialized

logger = logging.getLogger(__name__)

class OllamaProvider(BaseAIProvider):
    """Ollama AI provider implementation."""

    def __init__(self):
        """Initialize Ollama provider."""

        super().__init__()
        self.name = "ollama"

    @ensure_session_initialized
    async def test_availability(self) -> bool:
        """Test if Ollama is available."""

        try:
            async with self._session.get(f"{self.endpoint}/api/tags") as response:
                return response.status == 200

        except Exception as e:
            logger.debug(f"Ollama availability test failed: {e}")
            return False

    @ensure_session_initialized
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""

        payload = {
            "model": self.generation_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature)
            }
        }

        async with self._session.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama request failed: {error_text}")

            result = await response.json()
            return result.get("response", "")
