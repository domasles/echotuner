# Custom AI Providers

This guide shows how to add your own AI providers to EchoTuner's AI system.

## Overview

EchoTuner uses an auto-discovery system for AI providers. Any provider class that inherits from `BaseAIProvider` and is placed in the `providers/` directory will be automatically registered.

## Creating a Custom Provider

### 1. Basic Provider Structure

Create a new file in `api/providers/` (e.g., `my_provider.py`):

```python
from .base import BaseAIProvider
import logging

logger = logging.getLogger(__name__)

class MyCustomProvider(BaseAIProvider):
    """Custom AI provider implementation."""
    
    def __init__(self):
        """Initialize custom provider."""
        super().__init__()

        self.name = "mycustom"  # Must be lowercase, no "Provider" suffix

        # Override base settings if needed
        # self.endpoint = "https://api.your-provider.com"  # Override AI_ENDPOINT
        # self.headers = {"Authorization": f"Bearer {your_api_key}"}  # Add auth headers
    
    async def test_availability(self) -> bool:
        """Test if the custom provider is available."""

        try:
            async with self._session.get(
                f"{self.endpoint}/health",
                headers=self.headers,
                timeout=5
            ) as response:
                return response.status == 200

        except Exception as e:
            logger.debug(f"Custom AI availability test failed: {e}")
            return False
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using your custom AI API."""

        payload = {
            "model": self.generation_model,
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }

        async with self._session.post(
            f"{self.endpoint}/generate",  # Replace with your API endpoint
            headers=self.headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Custom provider request failed: {error_text}")

            result = await response.json()
            return result.get("text", "")  # Adjust based on your API response format
    
    async def get_embedding(self, text: str, **kwargs) -> list[float]:
        """Generate embeddings using your custom AI API."""

        if not self.embedding_model:
            raise Exception("No embedding model configured")

        payload = {
            "model": self.embedding_model,
            "input": text
        }

        async with self._session.post(
            f"{self.endpoint}/embeddings",  # Replace with your API endpoint
            headers=self.headers,
            json=payload,
            timeout=self.timeout
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Custom provider embedding request failed: {error_text}")

            result = await response.json()
            return result.get("embedding", [])  # Adjust based on your API response format
```

### 2. Environment Configuration

Add your provider's settings to your `.env` file:

```env
# Custom AI Provider
AI_PROVIDER=mycustom               # Must match your provider's name property
AI_ENDPOINT=https://api.your-provider.com
AI_GENERATION_MODEL=custom-model-v1
AI_EMBEDDING_MODEL=custom-embedding-v1
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_TIMEOUT=30

# Add any additional settings your provider needs
CLOUD_API_KEY=your_api_key_here    # If your provider uses this setting
```

### 3. Settings Configuration

The project uses a simple settings system that reads from environment variables. Check `config/settings.py` to see how your provider settings will be loaded:

```python
# The project automatically loads environment variables
# Your CLOUD_API_KEY will be available as settings.CLOUD_API_KEY
# Your AI_PROVIDER setting will determine which provider to use
```

### 4. Update AI Provider Setting

To use your custom provider as the default, update your `.env`:

```env
AI_PROVIDER=mycustom
```

## Advanced Provider Features

### Custom Configuration Validation

```python
class MyCustomProvider(BaseAIProvider):
    def __init__(self):
        super().__init__()
        self.name = "mycustom"

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate provider configuration."""

        if not self.api_key:
            raise ValueError("CLOUD_API_KEY is required")

        if not self.base_url:
            raise ValueError("AI_ENDPOINT is required")

        # Test connection
        try:
            response = httpx.get(f"{self.base_url}/health")
            response.raise_for_status()

        except Exception as e:
            logger.warning(f"Custom AI health check failed: {e}")
```

### Custom Model Selection

```python
class MyCustomProvider(BaseAIProvider):
    def __init__(self):
        super().__init__()
        self.name = "mycustom"

        # Support multiple models
        self.models = {
            "fast": "custom-fast-v1",
            "balanced": "custom-balanced-v1", 
            "creative": "custom-creative-v1"
        }

        self.default_model = self.models["balanced"]
    
    async def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text with model selection."""

        selected_model = model or self.default_model

        if selected_model not in self.models.values():
            logger.warning(f"Unknown model {selected_model}, using default")
            selected_model = self.default_model

        # Use selected_model in API call...
```

### Custom Error Handling

```python
class CustomAIError(Exception):
    """Custom AI provider specific error."""
    pass

class MyCustomProvider(BaseAIProvider):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            # API call...
            pass

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise CustomAIError("Rate limit exceeded")

            elif e.response.status_code == 401:
                raise CustomAIError("Invalid API key")

            else:
                raise CustomAIError(f"API error: {e.response.status_code}")

        except Exception as e:
            raise CustomAIError(f"Unexpected error: {e}")
```

### Streaming Support

```python
class MyCustomProvider(BaseAIProvider):
    async def generate_text_stream(self, prompt: str, **kwargs):
        """Generate text with streaming support."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        
        async with self.client.stream("POST", "/generate", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])

                    if "text" in data:
                        yield data["text"]
```

## Provider Testing

### Unit Tests

Create `tests/test_mycustom_provider.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from providers.my_provider import MyCustomProvider

@pytest.fixture
def provider():
    with patch.dict('os.environ', {
        'CLOUD_API_KEY': 'test_key',
        'AI_ENDPOINT': 'https://test.api.com'
    }):
        return MyCustomProvider()

@pytest.mark.asyncio
async def test_generate_text(provider):
    with patch.object(provider.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"text": "Generated text"}
        mock_post.return_value = mock_response

        result = await provider.generate_text("Test prompt")
        assert result == "Generated text"

@pytest.mark.asyncio
async def test_get_embedding(provider):
    with patch.object(provider.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_post.return_value = mock_response

        result = await provider.get_embedding("Test text")
        assert result == [0.1, 0.2, 0.3]
```

### Integration Tests

Test with a real API endpoint:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_integration():
    provider = MyCustomProvider()

    if not provider.is_available():
        pytest.skip("Custom AI provider not configured")

    result = await provider.generate_text("Hello, world!")

    assert isinstance(result, str)
    assert len(result) > 0
```

## Best Practices

### 1. Configuration Management

- Use environment variables for all configuration
- Provide sensible defaults where possible
- Validate configuration in `__init__`
- Document all required environment variables

### 2. Error Handling

- Implement robust error handling
- Use custom exception classes
- Log errors appropriately
- Provide meaningful error messages

### 3. Resource Management

- Use async HTTP clients
- Implement proper cleanup in `cleanup()` method
- Handle connection pooling efficiently
- Implement retry logic for transient failures

### 4. Performance

- Cache connections when possible
- Implement request/response caching if appropriate
- Use appropriate timeout values
- Monitor API usage and costs

### 5. Security

- Never log API keys or sensitive data
- Use HTTPS for all API calls
- Validate all inputs
- Implement proper authentication

## Troubleshooting

### Provider Not Loading

1. Check the file is in `api/providers/`
2. Ensure the class inherits from `BaseAIProvider`
3. Check for syntax errors in the provider file
4. Look at server logs for import errors

### Configuration Issues

1. Verify environment variables are set
2. Check settings.py includes your provider's config
3. Test with debug endpoints: `GET /ai/models`

### API Connection Problems

1. Test API endpoints manually with curl
2. Check network connectivity
3. Verify API keys and authentication
4. Check for rate limiting or quota issues

## Next Steps

- Review [Environment Configuration](environment.md) for advanced settings
- Check [Security Configuration](security.md) for security best practices
- See existing providers in `api/providers/` for more examples
