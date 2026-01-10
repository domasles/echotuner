"""
Custom AI Provider Template for EchoTuner API.

This is a template file that demonstrates how to create custom AI providers.
Copy this file and modify it to implement your own AI provider.

Example usage:
1. Copy this file to a new file (e.g., providers/my_custom_provider.py)
2. Implement the required methods
3. The provider will be auto-discovered by the registry
4. Set AI_PROVIDER=custom in your .env file (or whatever name you use)
"""

import logging

from typing import List

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class CustomProvider(BaseAIProvider):
    """
    Custom AI provider implementation template.

    Replace this class and its methods with your specific implementation.
    """

    def __init__(self):
        """Initialize the provider."""

        super().__init__()
        self.name = "custom"  # Change this to your provider name (lowercase)

        # Override any settings-based attributes if needed
        # self.endpoint = "https://your-custom-api.com"  # Override AI_ENDPOINT
        # self.headers = {"Authorization": f"Bearer {your_api_key}"}  # Add auth headers

    async def test_availability(self) -> bool:
        """
        Test if your provider is available.

        This should make a minimal request to test connectivity.
        Return True if available, False otherwise.
        """

        try:
            # Example: make a simple GET request to test connectivity
            response = await self._client.get(f"{self.endpoint}/health")
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Custom provider availability test failed: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using your provider.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Generated text response
        """

        # Example implementation - replace with your provider's API
        payload = {
            "prompt": prompt,
            "model": self.generation_model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        response = await self._client.post(
            f"{self.endpoint}/v1/generate",  # Replace with your API endpoint
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise Exception(f"Custom provider request failed: {response.text}")

        result = response.json()
        return result.get("text", "")  # Adjust based on your API response format


# Additional helper methods you might want to implement:


class AdvancedCustomProvider(CustomProvider):
    """
    Advanced custom provider template with additional features.
    """

    async def initialize(self) -> None:
        """
        Override initialization if you need custom setup.
        """

        await super().initialize()

        # Add your custom initialization logic here
        # For example: authenticate, validate API keys, etc.
        logger.info(f"Initializing {self.name} provider with custom setup")

    async def close(self) -> None:
        """
        Override cleanup if you need custom teardown.
        """

        # Add your custom cleanup logic here
        logger.info(f"Closing {self.name} provider")
        await super().close()

    def validate_config(self) -> List[str]:
        """
        Validate provider configuration.

        Returns:
            List of validation error messages (empty if valid)
        """

        errors = []

        if not self.endpoint:
            errors.append("AI_ENDPOINT is required")

        if not self.generation_model:
            errors.append("AI_GENERATION_MODEL is required")

        # Add your custom validation logic here
        # Example: check API keys, validate endpoint format, etc.

        return errors
