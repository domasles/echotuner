"""
Custom AI Provider Template for EchoTuner API.

This is a template file that demonstrates how to create custom AI providers.
Copy this file and modify it to implement your own AI provider.

Example usage:
1. Copy this file to a new file (e.g., providers/my_custom_provider.py)
2. Implement the required methods
3. Update ai_models.py to register your provider
4. Set AI_PROVIDER=my_custom in your .env file
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
    
    @property
    def name(self) -> str:
        """Return your provider's name."""
        return "Custom"  # Change this to your provider name
    
    @property
    def supports_embeddings(self) -> bool:
        """Return whether your provider supports embeddings."""
        return True  # Change to False if your provider doesn't support embeddings
    
    async def test_availability(self) -> bool:
        """
        Test if your provider is available.
        
        This should make a minimal request to test connectivity.
        Return True if available, False otherwise.
        """
        try:
            # Example: make a simple GET or POST request to test
            async with self._session.get(f"{self.endpoint}/health") as response:
                return response.status == 200
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
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "prompt": prompt,
            "model": self.generation_model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }

        async with self._session.post(
            f"{self.endpoint}/v1/generate",  # Replace with your API endpoint
            headers=headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Custom provider request failed: {error_text}")

            result = await response.json()
            return result.get("text", "")  # Adjust based on your API response format
    
    async def _get_embedding_impl(self, text: str, **kwargs) -> List[float]:
        """
        Get embedding using your provider.
        
        Args:
            text: The input text
            **kwargs: Additional parameters
            
        Returns:
            Embedding vector as list of floats
        """
        if not self.embedding_model:
            raise Exception("No embedding model configured for Custom provider")
        
        # Example implementation - replace with your provider's API
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        payload = {
            "text": text,
            "model": self.embedding_model
        }

        async with self._session.post(
            f"{self.endpoint}/v1/embeddings",  # Replace with your API endpoint
            headers=headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Custom provider embedding request failed: {error_text}")

            result = await response.json()
            return result.get("embedding", [])  # Adjust based on your API response format

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
            errors.append("Endpoint is required")
        
        if not self.generation_model:
            errors.append("Generation model is required")
        
        # Add your custom validation logic here
        
        return errors
