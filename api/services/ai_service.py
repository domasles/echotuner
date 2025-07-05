"""
AI service.
Handles AI model interactions across different providers (Ollama, OpenAI, Anthropic, etc.).
"""

import aiohttp
import logging

from typing import Dict, Any, Optional, List

from core.singleton import SingletonServiceBase

from config.ai_models import ai_model_manager, AIModelConfig

logger = logging.getLogger(__name__)

class AIService(SingletonServiceBase):
    """Service for interacting with AI models across different providers."""
    
    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the AIService."""

        self._session: Optional[aiohttp.ClientSession] = None
        self._log_initialization("AI service initialized successfully", logger)
    
    async def initialize(self):
        """Initialize the AI service."""

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            default_provider = ai_model_manager.get_provider()
            await self._test_model_availability(default_provider)
            logger.info(f"AI Service initialized with {default_provider.name}")

        except Exception as e:
            logger.warning(f"Default AI model not available: {e}")

    async def close(self):
        """Close the AI service and cleanup resources."""

        if self._session:
            await self._session.close()
            self._session = None

    async def _test_model_availability(self, model_config: AIModelConfig) -> bool:
        """Test if a model is available and responding."""

        try:
            if model_config.name.lower() == "ollama":
                async with self._session.get(f"{model_config.endpoint}/api/tags") as response:
                    return response.status == 200

            elif model_config.name.lower() == "openai":
                headers = model_config.headers or {}
                headers["Content-Type"] = "application/json"

                test_payload = {
                    "model": model_config.model_name,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5
                }

                async with self._session.post(
                    f"{model_config.endpoint}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

            elif model_config.name.lower() == "anthropic":
                headers = model_config.headers or {}
                headers["Content-Type"] = "application/json"

                test_payload = {
                    "model": model_config.model_name,
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                async with self._session.post(
                    f"{model_config.endpoint}/messages",
                    headers=headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

            return True

        except Exception as e:
            logger.debug(f"Model availability test failed for {model_config.name}: {e}")
            return False

    async def generate_text(self, prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
        """Generate text using the specified AI model."""

        model_config = ai_model_manager.get_provider(model_id)

        try:
            if model_config.name.lower() == "ollama":
                return await self._generate_ollama(prompt, model_config, **kwargs)

            elif model_config.name.lower() == "openai":
                return await self._generate_openai(prompt, model_config, **kwargs)

            elif model_config.name.lower() == "anthropic":
                return await self._generate_anthropic(prompt, model_config, **kwargs)

            else:
                raise Exception(f"Unsupported AI provider: {model_config.name}")

        except Exception as e:
            logger.error(f"Text generation failed with {model_config.name}: {e}")
            raise Exception(f"Text generation failed: {e}")

    async def _generate_ollama(self, prompt: str, model_config: AIModelConfig, **kwargs) -> str:
        """Generate text using Ollama."""

        payload = {
            "model": model_config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", model_config.temperature or 0.7),
                "num_predict": kwargs.get("max_tokens", model_config.max_tokens or 2000)
            }
        }

        async with self._session.post(
            f"{model_config.endpoint}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=model_config.timeout)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama request failed: {error_text}")

            result = await response.json()
            return result.get("response", "")

    async def _generate_openai(self, prompt: str, model_config: AIModelConfig, **kwargs) -> str:
        """Generate text using OpenAI."""

        headers = model_config.headers or {}
        headers["Content-Type"] = "application/json"

        payload = {
            "model": model_config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", model_config.max_tokens or 2000),
            "temperature": kwargs.get("temperature", model_config.temperature or 0.7)
        }

        async with self._session.post(
            f"{model_config.endpoint}/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=model_config.timeout)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI request failed: {error_text}")

            result = await response.json()
            return result["choices"][0]["message"]["content"]

    async def _generate_anthropic(self, prompt: str, model_config: AIModelConfig, **kwargs) -> str:
        """Generate text using Anthropic Claude."""

        headers = model_config.headers or {}
        headers["Content-Type"] = "application/json"

        payload = {
            "model": model_config.model_name,
            "max_tokens": kwargs.get("max_tokens", model_config.max_tokens or 2000),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", model_config.temperature or 0.7)
        }

        async with self._session.post(
            f"{model_config.endpoint}/messages",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=model_config.timeout)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic request failed: {error_text}")

            result = await response.json()
            return result["content"][0]["text"]

    async def get_embedding(self, text: str, model_id: Optional[str] = None) -> List[float]:
        """Get text embedding using the specified model."""

        model_config = ai_model_manager.get_provider(model_id)

        if not model_config.embedding_model:
            raise Exception(f"No embedding model configured for {model_config.name}")

        try:
            if model_config.name.lower() == "ollama":
                return await self._get_ollama_embedding(text, model_config)

            else:
                raise Exception(f"Embedding not supported for {model_config.name}")

        except Exception as e:
            logger.error(f"Embedding generation failed with {model_config.name}: {e}")
            raise Exception(f"Embedding generation failed: {e}")

    async def _get_ollama_embedding(self, text: str, model_config: AIModelConfig) -> List[float]:
        """Get embedding using Ollama."""

        payload = {
            "model": model_config.embedding_model,
            "prompt": text
        }

        async with self._session.post(
            f"{model_config.endpoint}/api/embeddings",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=model_config.timeout)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama embedding request failed: {error_text}")

            result = await response.json()
            return result.get("embedding", [])

    def list_available_models(self) -> List[str]:
        """List all available AI models."""

        return ai_model_manager.list_models()

    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""

        model_config = ai_model_manager.get_provider(model_id)

        return {
            "name": model_config.name,
            "endpoint": model_config.endpoint,
            "model_name": model_config.model_name,
            "embedding_model": model_config.embedding_model,
            "has_api_key": bool(model_config.api_key),
            "timeout": model_config.timeout,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature
        }

ai_service = AIService()
