"""
Google Gemini AI Provider for EchoTuner API.

This module implements the Google Gemini provider for cloud AI models.
"""

import logging

from typing import List

from domain.config.settings import settings

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class GoogleProvider(BaseAIProvider):
    """Google Gemini AI provider implementation."""

    def __init__(self):
        """Initialize Google provider."""

        super().__init__()

        self.name = "google"
        self.headers = {"x-goog-api-key": settings.CLOUD_API_KEY}

    async def test_availability(self) -> bool:
        """Test if Google Gemini is available."""

        try:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"

            test_payload = {"contents": [{"parts": [{"text": "Hi"}]}], "generationConfig": {"maxOutputTokens": 1}}

            response = await self._client.post(
                f"{self.endpoint}/v1beta/models/{self.generation_model}:generateContent",
                headers=headers,
                json=test_payload,
                timeout=5,
            )
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Google availability test failed: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Google Gemini."""

        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        response = await self._client.post(
            f"{self.endpoint}/v1beta/models/{self.generation_model}:generateContent",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise Exception(f"Google request failed: {response.text}")

        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
