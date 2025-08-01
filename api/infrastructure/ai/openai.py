"""
OpenAI AI Provider for EchoTuner API.

This module implements the OpenAI provider for cloud AI models.
"""

import logging

from typing import List

from .base import BaseAIProvider

from domain.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI AI provider implementation."""
    
    def __init__(self):
        """Initialize OpenAI provider."""

        super().__init__()
        
        self.name = "openai"
        self.headers = {"Authorization": f"Bearer {settings.CLOUD_API_KEY}"}

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

            response = await self._client.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            return response.status_code == 200

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

        response = await self._client.post(
            f"{self.endpoint}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI request failed: {response.text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]
