![EchoTuner Logo](../EchoTunerLogo.svg)

# EchoTuner API - AI-Powered Playlist Generation Backend

## Security & Production Updates

**Latest Security Enhancements:**
- **Session Management**: Secure OAuth2 with automatic expiration and cleanup
- **Rate Limiting**: User-based limits (not device-based) for consistent experience across devices
- **Input Validation**: Enhanced sanitization and length restrictions
- **CORS Security**: Environment-specific origin restrictions
- **Security Headers**: OWASP-recommended headers in production mode
- **Configuration Validation**: Startup validation ensures production readiness

**Docker Ready**: Multi-stage builds with API + Flutter web deployment support.

---

The EchoTuner API is a production-ready RESTful service that generates personalized music playlists using artificial intelligence and natural language processing. This backend service powers the EchoTuner platform with intelligent music recommendations through flexible AI model support and real-time Spotify integration.

**Current Version: 1.6.0**

## Overview

The API provides intelligent playlist generation capabilities with support for multiple AI providers including local Ollama models, OpenAI, Anthropic Claude, and custom AI endpoints. Built with FastAPI, it offers asynchronous request processing, comprehensive error handling, and seamless integration capabilities for third-party applications.

**Key Features:**
- **Flexible AI Models**: Support for Ollama (local), OpenAI, Anthropic Claude, and custom endpoints
- **Real-Time Processing**: Live Spotify search integrated with AI analysis
- **User Personality System**: Comprehensive preference learning and application
- **Production Hardened**: Comprehensive error handling with graceful failures
- **Integration Ready**: RESTful API designed for both internal app and external integration
- **Configurable Rate Limiting**: Independent playlist and refinement limits with backend control

## AI Model Support

**Local AI (Ollama) - Default**
- **Generation Model**: `llama3.2:3b` for intelligent playlist strategy generation
- **Validation Model**: `nomic-embed-text` for semantic prompt validation
- **Benefits**: No API costs, privacy, offline capability
- **Requirements**: Local Ollama installation

**Cloud AI Providers**
- **OpenAI**: `gpt-4o-mini` for fast, intelligent responses
- **Anthropic Claude**: `claude-3-5-sonnet-20241022` for sophisticated analysis
- **Benefits**: No local resources, powerful models, consistent performance
- **Requirements**: Valid API keys

**Custom AI Models**
- Support for any REST API-based AI service
- Configurable endpoints, headers, and parameters
- Extensible architecture for future providers

**Spotify Web API Integration (Required)**
- **Real-Time Search**: Live access to Spotify's music catalog
- **Current Music Data**: No static databases, always up-to-date content
- **Authenticated Access**: Requires valid Spotify Developer credentials

## Quick Start

For complete installation and setup instructions, please refer to the [master installation guide](../README.md#installation) in the project root.

### Prerequisites

1. **Python 3.8+** installed on your system
2. **AI Model Provider** - Choose one:
   - **Ollama** (local) from [https://ollama.ai](https://ollama.ai)
   - **OpenAI API Key** from [https://platform.openai.com](https://platform.openai.com)
   - **Anthropic API Key** from [https://console.anthropic.com](https://console.anthropic.com)
3. **Spotify Developer Account** for API credentials
4. **Spotify API credentials** (Client ID and Client Secret)

### Installation

1. **Navigate to API directory:**
   ```bash
   cd echotuner/api
   ```

2. **Copy over .env.sample to .env:**
    ```bash
    cp .env.sample .env
    ```

3. **Configure Spotify API credentials in `.env` file:**
   ```env
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   ```

4. **Configure your AI model:**

   **For Ollama (Local AI - Default):**
   ```bash
   # Install and start Ollama
   # Install required models
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text
   ```

   **For OpenAI (Cloud AI):**
   ```env
   # Edit .env file
   DEFAULT_AI_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

   **For Anthropic Claude (Cloud AI):**
   ```env
   # Edit .env file
   DEFAULT_AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```

5. **Run automated setup:**
   ```bash
   python setup.py
   ```

6. **Start the API:**
   ```bash
   python main.py
   ```

## API Endpoints

### Core Functionality

#### `POST /generate-playlist`
Generate a new playlist based on natural language prompt.

**Request Body:**
```json
{
    "prompt": "I need upbeat indie rock for a morning workout",
    "device_id": "unique_device_identifier",
    "count": 20,
    "user_context": {
        "favorite_genres": ["indie", "rock", "alternative"],
        "favorite_artists": ["Arctic Monkeys", "The Strokes"],
        "energy_preference": "high"
    }
}
```

#### `POST /refine-playlist`
Refine existing playlist with additional feedback.

#### `GET /rate-limit-status/{device_id}`
Check current rate limiting status for a device.

#### `GET /health`
Service health and dependency status.

### Authentication Endpoints

#### `GET /auth/init`
Initialize Spotify OAuth authentication flow.

**Query Parameters:**
- `device_id`: Unique device identifier  
- `platform`: Platform type (web, android, ios, desktop)

#### `GET /auth/callback`
Handle Spotify OAuth callback and create authenticated session.

#### `POST /auth/validate`  
Validate existing authentication session.

**Request Body:**
```json
{
    "session_id": "uuid4_session_id",
    "device_id": "device_identifier"
}
```

For complete API documentation and examples, refer to the [API Reference](../README.md#api-reference) in the master documentation.

## Configuration

The API uses environment variables for configuration. Key settings include:

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

DEBUG=true
LOG_LEVEL=INFO

DATABASE_FILENAME=echotuner.db

# Ollama Configuration (for AI models)
USE_OLLAMA=true
OLLAMA_TIMEOUT=30
OLLAMA_MODEL_PULL_TIMEOUT=300

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VALIDATION_MODEL=nomic-embed-text:latest
OLLAMA_GENERATION_MODEL=phi3:mini

PROMPT_VALIDATION_THRESHOLD=0.6 # Threshold for prompt validation (0.0 to 1.0)
PROMPT_VALIDATION_TIMEOUT=30    # Prompt validation timeout in seconds

# Spotify Configuration (for real-time song search)
# Get these from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri_here

# Authentication Settings
AUTH_REQUIRED=true

# Rate Limiting Settings
PLAYLIST_LIMIT_ENABLED=false
REFINEMENT_LIMIT_ENABLED=false

MAX_PLAYLISTS_PER_DAY=3
MAX_SONGS_PER_PLAYLIST=30
MAX_REFINEMENTS_PER_PLAYLIST=3

SESSION_TIMEOUT=24 # Session expiration in hours

# Cache Settings
CACHE_ENABLED=true

# Security Configuration
MAX_AUTH_ATTEMPTS_PER_IP=10
AUTH_ATTEMPT_WINDOW_MINUTES=60
SECURE_HEADERS=true
```

For complete configuration options, see the [Configuration](../README.md#configuration) section in the master documentation.

## Development and Testing

### Deployment

For production deployment instructions, container deployment, and integration examples, refer to the [Deployment](../README.md#deployment) and [Integration](../README.md#integration) sections in the master documentation.

## System Requirements

- **CPU**: Modern multi-core processor (4+ cores recommended)
- **RAM**: 8GB (4GB for Ollama models, 4GB for application)
- **Storage**: 3GB available space (2GB for AI models, 1GB for application)
- **Network**: Stable internet connection for Spotify API access

For detailed system requirements and performance optimization, see [System Requirements](../README.md#system-requirements) in the master documentation.

## Support

For detailed troubleshooting, performance optimization, and support information, please refer to the [master documentation](../README.md).

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Refer to the master README and inline code documentation
- **Development**: Follow the contributing guidelines in the project root

## Database Schema

The API uses SQLite with the following key tables:

**auth_sessions**: Session management
- `session_id` (TEXT PRIMARY KEY) - UUID4 session identifier
- `device_id` (TEXT NOT NULL) - Unique device identifier
- `spotify_user_id` (TEXT) - Spotify user ID  
- `access_token` (TEXT) - Spotify access token
- `created_at` (INTEGER) - Session creation timestamp

**auth_states**: OAuth state validation
- `state` (TEXT PRIMARY KEY) - OAuth state parameter
- `device_id` (TEXT NOT NULL) - Associated device
- `expires_at` (INTEGER) - State expiration timestamp

## AI Model Configuration

EchoTuner supports multiple AI providers that can be easily configured through environment variables. The system automatically handles fallbacks and provides a unified interface for all providers.

### AI Model Management

The API includes built-in endpoints to manage AI models:

- **`GET /ai/models`** - List all available AI models and their configurations
- **`POST /ai/test`** - Test a specific AI model with a simple prompt

### Supported AI Providers

#### 1. Ollama (Local AI - Default)
**Best for**: Privacy, no API costs, offline usage

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Install required models
ollama pull phi3:mini              # Generation model
ollama pull nomic-embed-text       # Embedding model
```

**Configuration:**
```env
DEFAULT_AI_PROVIDER=ollama
AI_ENDPOINT=http://localhost:11434
AI_GENERATION_MODEL=phi3:mini
AI_EMBEDDING_MODEL=nomic-embed-text:latest
```

#### 2. OpenAI (Cloud AI)
**Best for**: Fast responses, powerful reasoning, no local resources

**Requirements:**
- OpenAI API account at [https://platform.openai.com](https://platform.openai.com)
- API key with sufficient credits

**Configuration:**
```env
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Models used:**
- **Generation**: `gpt-4o-mini` (configurable)
- **Cost**: ~$0.15-0.60 per 1000 requests (depending on prompt size)

#### 3. Anthropic Claude (Cloud AI)
**Best for**: Sophisticated analysis, creative responses

**Requirements:**
- Anthropic account at [https://console.anthropic.com](https://console.anthropic.com)
- API key with sufficient credits

**Configuration:**
```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Models used:**
- **Generation**: `claude-3-5-sonnet-20241022` (configurable)
- **Cost**: ~$3-15 per 1000 requests (depending on prompt size)

#### 4. Custom AI Providers

EchoTuner's AI system is designed to be modular and extensible. You can add support for any REST API-based AI service by following these steps:

##### Step 1: Environment Configuration

Add your AI provider's configuration to the `.env` file:

```env
# Custom AI Provider Configuration
CUSTOM_PROVIDER_API_KEY=your-api-key-here
CUSTOM_PROVIDER_ENDPOINT=https://api.yourprovider.com/v1
CUSTOM_PROVIDER_MODEL=your-model-name
CUSTOM_PROVIDER_TIMEOUT=30
```

Update `config/settings.py` to include your new provider settings:

```python
class Settings:
    # Add your custom provider settings
    CUSTOM_PROVIDER_API_KEY: Optional[str] = os.getenv("CUSTOM_PROVIDER_API_KEY")
    CUSTOM_PROVIDER_ENDPOINT: str = os.getenv("CUSTOM_PROVIDER_ENDPOINT", "https://api.yourprovider.com/v1")
    CUSTOM_PROVIDER_MODEL: str = os.getenv("CUSTOM_PROVIDER_MODEL", "default-model")
    CUSTOM_PROVIDER_TIMEOUT: int = int(os.getenv("CUSTOM_PROVIDER_TIMEOUT", 30))
```

##### Step 2: Register the Model

In `config/ai_models.py`, add your provider to the `_setup_default_models` method:

```python
def _setup_default_models(self):
    # ... existing models ...
    
    # Your Custom Provider
    if settings.CUSTOM_PROVIDER_API_KEY:
        self._models["custom_provider"] = AIModelConfig(
            name="Custom Provider",
            endpoint=settings.CUSTOM_PROVIDER_ENDPOINT,
            api_key=settings.CUSTOM_PROVIDER_API_KEY,
            model_name=settings.CUSTOM_PROVIDER_MODEL,
            headers={
                "Authorization": f"Bearer {settings.CUSTOM_PROVIDER_API_KEY}",
                "Content-Type": "application/json"
            },
            max_tokens=2000,
            temperature=0.7,
            timeout=settings.CUSTOM_PROVIDER_TIMEOUT
        )
```

##### Step 3: Implement the AI Service Logic

In `services/ai_service.py`, add your provider to the `generate_text` method:

```python
async def generate_text(self, prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
    model_config = ai_model_manager.get_model(model_id)
    
    try:
        if model_config.name.lower() == "ollama":
            return await self._generate_ollama(prompt, model_config, **kwargs)
        elif model_config.name.lower() == "openai":
            return await self._generate_openai(prompt, model_config, **kwargs)
        elif model_config.name.lower() == "anthropic":
            return await self._generate_anthropic(prompt, model_config, **kwargs)
        elif model_config.name.lower() == "custom provider":  # Add this
            return await self._generate_custom_provider(prompt, model_config, **kwargs)
        else:
            raise AIServiceError(f"Unsupported AI provider: {model_config.name}")
    except Exception as e:
        logger.error(f"Text generation failed with {model_config.name}: {e}")
        raise AIServiceError(f"Text generation failed: {e}")
```

##### Step 4: Implement the Provider Method

Add the implementation method for your provider:

```python
async def _generate_custom_provider(self, prompt: str, model_config: AIModelConfig, **kwargs) -> str:
    """Generate text using Custom Provider."""
    headers = model_config.headers or {}
    
    # Customize this payload based on your provider's API specification
    payload = {
        "model": model_config.model_name,
        "prompt": prompt,  # or "messages": [{"role": "user", "content": prompt}]
        "max_tokens": kwargs.get("max_tokens", model_config.max_tokens or 2000),
        "temperature": kwargs.get("temperature", model_config.temperature or 0.7)
    }
    
    async with self._session.post(
        f"{model_config.endpoint}/generate",  # Adjust endpoint path as needed
        headers=headers,
        json=payload,
        timeout=aiohttp.ClientTimeout(total=model_config.timeout)
    ) as response:
        if response.status != 200:
            error_text = await response.text()
            raise AIServiceError(f"Custom Provider request failed: {error_text}")
        
        result = await response.json()
        
        # Adjust this based on your provider's response format
        return result.get("response", "")  # or result["choices"][0]["text"], etc.
```

##### Step 5: Test Your Integration

1. **Start the API in debug mode**:
   ```bash
   python main.py
   ```

2. **Check available models** (debug mode only):
   ```bash
   curl "http://localhost:8000/ai/models"
   ```

3. **Test your model** (debug mode only):
   ```bash
   curl -X POST "http://localhost:8000/ai/test" \
     -H "Content-Type: application/json" \
     -d '{"model_id": "custom_provider", "prompt": "Hello, world!"}'
   ```

4. **Generate a playlist** using your model:
   ```bash
   curl -X POST "http://localhost:8000/generate-playlist" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Upbeat rock music for working out",
       "device_id": "test-device",
       "count": 10
     }'
   ```

##### Common Integration Patterns

**OpenAI-Compatible APIs**: Many providers use OpenAI-compatible endpoints. For these, you can often reuse the OpenAI implementation.

**Custom Response Formats**: If your provider returns a different response format, adjust the parsing in your implementation method.

**Error Handling**: Always include proper error handling for timeouts, connection errors, and API-specific errors.

**Security**: Never log or expose API keys, validate inputs, implement rate limiting, and use timeouts to prevent hanging requests.
