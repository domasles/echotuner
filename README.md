![EchoTuner Logo](./EchoTunerLogo.svg)

# EchoTuner - AI Powered Playlist Generation Platform

EchoTuner is a production-ready platform that generates personalized music playlists using artificial intelligence and natural language processing. The platform features a flexible AI model system supporting both local (Ollama) and cloud-based AI providers (OpenAI, Anthropic Claude), combined with Spotify Web API integration for intelligent music recommendations.

The platform consists of a modular RESTful API service and a cross-platform Flutter application for music discovery and playlist creation.

**Current Version: 1.6.0**

## Project Status

EchoTuner is now feature-complete with both API backend and user application ready for production deployment.

**Platform Components:**
- **API Backend**: Complete and production-ready with modular architecture
- **Flutter Application**: Complete cross-platform app (Android, iOS, Web, Desktop)
- **AI Model System**: Flexible support for multiple AI providers
- **Database Layer**: Centralized, modular database service

**Key Features:**
- **Flexible AI Models**: Support for Ollama (local), OpenAI, Anthropic Claude, and custom endpoints
- **Real-Time Processing**: Live Spotify search integrated with AI analysis
- **User Personality System**: Comprehensive user preference learning and application
- **Cross-Platform Support**: Single codebase for all major platforms
- **Production Hardened**: Comprehensive error handling with graceful failures
- **Modular Architecture**: Clean separation of concerns with reusable services
- **Integration Ready**: RESTful API designed for both internal app and external integration

## Architecture Overview

### Modular Backend Design

**Database Service**
- Centralized database operations with async support
- Consistent error handling and connection management
- Modular operations for auth, personality, playlists, and rate limiting
- Clean separation between business logic and data access

**Service Layer**
- Auth Service: OAuth2 authentication and session management
- Personality Service: User preference learning and Spotify integration  
- Playlist Generator: AI-powered playlist creation with discovery strategies
- Rate Limiter: Request throttling and usage analytics
- Spotify Services: Search, playlist management, and artist recommendations

### AI Model Support

**Local AI (Ollama)**
- **Default Model**: `llama3.2:3b` for intelligent playlist generation
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

### Service Architecture

**FastAPI Backend**
- Asynchronous request processing with flexible AI model routing
- Comprehensive error handling and logging
- Rate limiting and abuse prevention
- Health monitoring and status endpoints

**AI Pipeline**
- **Prompt Validation**: Semantic analysis to ensure music-related requests
- **Strategy Generation**: AI-powered mood and genre analysis
- **Model Fallback**: Automatic switching between available AI providers
- **Music Search**: Real-time Spotify API integration
- **Result Processing**: Intelligent song selection and playlist assembly

**Application Layer** (Coming Soon)
- Direct user interface for playlist creation
- Advanced playlist management and curation
- Personalized music discovery features
- Seamless integration with popular music streaming services

## Quick Start Guide

### Prerequisites

Before setting up EchoTuner, ensure you have:

1. **Python 3.8+** for the API backend
2. **Dart SDK** (latest stable) for the Flutter app
3. **AI Model Provider** - Choose one:
   - **Ollama** (local, free) from [https://ollama.ai](https://ollama.ai)
   - **OpenAI API Key** (cloud, paid) from [https://platform.openai.com](https://platform.openai.com)
   - **Anthropic API Key** (cloud, paid) from [https://console.anthropic.com](https://console.anthropic.com)
4. **Spotify Developer Account** and API credentials from [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/echotuner.git
cd echotuner
```

#### 2. API Backend Setup
```bash
cd api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.sample .env
# Edit .env with your configuration (see API Setup section below)

# Run the API
python main.py
```

#### 3. Flutter App Setup
```bash
cd ../app

# Install dependencies
dart pub get

# Generate JSON serialization code
dart run build_runner build --delete-conflicting-outputs

# Configure environment
cp .env.sample .env
# Edit .env with your API host configuration

# Run the app
dart run
```

### Detailed Setup Guides

For comprehensive setup instructions including AI model configuration:
- **[API Backend Setup](api/README.md)** - Detailed API installation and configuration
- **[Flutter App Setup](app/README.md)** - Mobile and desktop app development setup

## Features

### Core Capabilities
- **Natural Language Processing**: Understands complex mood and preference descriptions
- **AI-Powered Strategy Generation**: Uses local Ollama models for intelligent music analysis
- **Real-Time Music Discovery**: Live integration with Spotify's current catalog
- **Exact Count Control**: Guarantees precise playlist sizes (5-50+ songs) (only available in API's debug mode)
- **Playlist Refinement**: Iterative improvement based on user feedback
- **Semantic Validation**: Ensures requests are music-related using AI embeddings
- **Smart Rate Limiting**: Configurable limits with visual indicators and conditional enforcement

### Production Architecture
- **Zero-Fallback Design**: Requires all dependencies to be operational for consistent quality
- **Rate Limiting**: Configurable daily limits and request quotas
- **Health Monitoring**: Built-in status checks for all service dependencies
- **Error Transparency**: Clear error messages when dependencies are unavailable
- **Configuration Management**: Environment-based setup for different deployment scenarios

### Privacy and Security
- **Local AI Processing**: All AI inference runs on your infrastructure
- **No External AI APIs**: Complete independence from cloud AI services
- **Hashed Device IDs**: User anonymity through cryptographic hashing
- **No Data Persistence**: User prompts and preferences are not stored permanently

## AI Model Configuration

EchoTuner supports multiple AI providers with automatic model selection and flexible configuration. This allows users to choose between cost-effective local models or powerful cloud-based AI services.

### Supported AI Models

#### Ollama (Local AI - Default)
- **Models**: `phi3:mini` for generation, `nomic-embed-text` for embeddings
- **Benefits**: No API costs, complete privacy, offline capability
- **Requirements**: Local Ollama installation and model download
- **Cost**: Free (after initial hardware investment)

**Setup:**

Install and start Ollama
```bash
ollama pull phi3:mini
ollama pull nomic-embed-text
```

#### OpenAI (Cloud AI)
- **Model**: `gpt-4o-mini` for fast, intelligent responses
- **Benefits**: Fast responses, powerful reasoning, no local resources required
- **Requirements**: OpenAI API key with credits
- **Cost**: ~$0.15-0.60 per 1000 requests

**Setup:**
```env
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
```

#### Anthropic Claude (Cloud AI)
- **Model**: `claude-3-5-sonnet-20241022` for sophisticated analysis
- **Benefits**: Advanced reasoning, creative responses, reliable performance  
- **Requirements**: Anthropic API key with credits
- **Cost**: ~$3-15 per 1000 requests

**Setup:**
```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

#### Custom AI Providers
The system supports any REST API-based AI service. See the [API documentation](api/README.md#setting-up-a-new-ai-model) for details on adding new providers.

### Why Multiple AI Providers?

**For Individual Users:**
- **Local Ollama**: Perfect for privacy-conscious users or those wanting to avoid ongoing costs
- **Cloud APIs**: Ideal for users who prefer convenience and don't mind pay-per-use pricing

**For Organizations:**
- **Cost Control**: Choose between upfront hardware costs (Ollama) vs. operational API costs
- **Compliance**: Local processing ensures data never leaves your infrastructure
- **Scalability**: Cloud APIs handle traffic spikes without infrastructure management

**For Open Source Projects:**
- **Accessibility**: Users can choose their preferred cost/convenience balance
- **No Lock-in**: Easy switching between providers based on needs
- **Development Flexibility**: Contributors can use different models for testing
- **Benefits**: Sophisticated analysis, strong reasoning capabilities
- **Requirements**: Anthropic API key
- **Configuration**: Set `ANTHROPIC_API_KEY` in environment variables

```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

#### Custom AI Models
EchoTuner supports any REST API-based AI service through its extensible architecture. You can add new AI providers by:

1. **Environment Configuration**: Add API keys and endpoints to `.env`
2. **Model Registration**: Register the provider in `config/ai_models.py`
3. **Service Implementation**: Add generation logic in `services/ai_service.py`
4. **Testing**: Use debug endpoints to validate integration

Common patterns include OpenAI-compatible APIs, custom response formats, and provider-specific authentication. The system handles automatic fallback, error handling, and secure API key management.

For detailed implementation instructions, see the [API README](./api/README.md#4-custom-ai-providers).

### Model Selection Logic
1. Uses model specified in `DEFAULT_AI_PROVIDER` environment variable
2. Falls back to Ollama if default model is unavailable
3. Automatic failover between available models
4. Graceful error handling with informative messages

### Authentication and Session Management
- **Spotify OAuth Integration**: Secure OAuth 2.0 flow with authorization code grant
- **Session-Based Authentication**: UUID4-based session IDs with automatic expiration
- **Cross-Platform Support**: Consistent authentication across web, mobile, and desktop
- **Session Security**: Device binding prevents session hijacking and spoofing
- **Token Management**: Secure refresh token handling with automatic renewal

## API Reference

### Core Endpoints

#### `POST /generate-playlist`
Generate a new playlist based on natural language prompt.

**Request Body:**
```json
{
    "prompt": "I need upbeat indie rock for a morning workout",
    "device_id": "unique_device_identifier",
    "count": 1,
    "user_context": {
        "favorite_genres": ["indie", "rock", "alternative"],
        "favorite_artists": ["Arctic Monkeys", "The Strokes"],
        "energy_preference": "high"
    }
}
```

**Response:**
```json
{
    "songs": [
        {
        "title": "Do I Wanna Know?",
        "artist": "Arctic Monkeys",
        "album": "AM",
        "spotify_id": "5FVd6KXrgO9B3JPmC8OPst",
        "popularity": 85,
        "genres": ["indie rock", "alternative rock"]
        }
    ],
    "generated_from": "I need upbeat indie rock for a morning workout",
    "total_count": 1,
    "is_refinement": false,
}
```

#### `POST /refine-playlist`
Refine existing playlist with additional feedback.

**Request Body:**
```json
{
    "prompt": "Make the playlist include more energetic songs",
    "device_id": "unique_device_identifier",
    "current_songs": [...],
    "count": 25
}
```

#### `GET /rate-limit-status/{device_id}`
Check current rate limiting status for a device.

**Response:**
```json
{
    "device_id": "hashed_device_id",
    "requests_made_today": 3,
    "max_requests_per_day": 10,
    "refinements_used": 1,
    "max_refinements": 3,
    "can_make_request": true,
    "can_refine": true,
    "playlist_limit_enabled": true,
    "refinement_limit_enabled": true
}
```

#### `GET /health`
Service health and dependency status.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.6.0",
    "services": {
        "prompt_validator": true,
        "playlist_generator": true,
        "rate_limiter": true
    },
    "features": {
        "spotify_search": true,
        "ai_generation": true,
        "rate_limiting": false
    }
}
```

### Authentication Endpoints

#### `GET /auth/init`
Initialize Spotify OAuth authentication flow.

**Query Parameters:**
- `device_id`: Unique device identifier
- `platform`: Platform type (web, android, ios, desktop)

**Response:**
```json
{
    "auth_url": "https://accounts.spotify.com/authorize?...",
    "state": "uuid4_state_parameter"
}
```

#### `GET /auth/callback`
Handle Spotify OAuth callback (used by Spotify, not directly by app).

#### `POST /auth/validate`
Validate existing authentication session.

**Request Body:**
```json
{
    "session_id": "uuid4_session_id",
    "device_id": "device_identifier"
}
```

**Response:**
```json
{
    "valid": true,
    "spotify_user_id": "spotify_user_123",
    "expires_at": 1703980800
}
```

## Configuration

### Environment Variables

#### API
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

#### App
```bash
# API Configuration
API_HOST=localhost
API_PORT=8000

# Development flags
DEBUG_MODE=true
ENABLE_LOGGING=true
```

You can set these variables in a `.env` file. Both the API and the application will automatically load their own `.env` file at startup.

### Rate Limiting Configuration

- **Development**: Set `PLAYLIST_LIMIT_ENABLED=false` and `REFINEMENT_LIMIT_ENABLED=false` for unlimited testing
- **Production**: Enable individual limits with appropriate daily quotas
- **Selective Control**: Enable/disable playlist and refinement limits independently

## Development and Testing

### Health Monitoring

```bash
# Check API health
curl http://localhost:8000/health

# Verify Ollama connectivity
curl http://localhost:11434/api/tags

# Test playlist generation
curl -X POST http://localhost:8000/generate-playlist \
    -H "Content-Type: application/json" \
    -d '{"prompt":"relaxing jazz for studying","device_id":"test","count":10}'
```

## System Requirements

### Required Dependencies
- **Ollama**: Must be installed and running with required models
    - `nomic-embed-text` model for prompt validation
    - `phi3:mini` model for playlist generation
- **Spotify Developer Account**: Valid API credentials required
- **Internet Connection**: Required for Spotify API access

### Minimum Hardware Requirements
- **CPU**: Modern multi-core processor (4+ cores recommended)
- **RAM**: 8GB (4GB for Ollama models, 4GB for application)
- **Storage**: 3GB available space (2GB for AI models, 1GB for application)
- **Network**: Stable internet connection for Spotify API access

### Recommended Hardware Specifications
- **CPU**: 8+ cores for optimal AI inference performance
- **RAM**: 16GB for handling concurrent requests efficiently
- **Storage**: SSD for faster model loading and response times
- **Network**: High-bandwidth connection for real-time music search

## Deployment

### Production Deployment

1. **Configure Production Environment**
```bash
# Set production values in .env
DEBUG=false
PLAYLIST_LIMIT_ENABLED=true
REFINEMENT_LIMIT_ENABLED=true
MAX_PLAYLISTS_PER_DAY=3
LOG_LEVEL=WARNING
```

2. **Process Management**
```bash
# Using systemd (Linux)
sudo systemctl enable echotuner
sudo systemctl start echotuner

# Using PM2 (Node.js process manager)
pm2 start "python main.py" --name echotuner
```

3. **Reverse Proxy Configuration**
```nginx
# Nginx configuration
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Container Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## Integration

### Client Libraries

EchoTuner's REST API can be integrated with any HTTP client. Example integration patterns:

**Python Client**
```python
import requests

def generate_playlist(prompt, device_id, count=20):
    response = requests.post(
        "http://localhost:8000/generate-playlist",
        json={
            "prompt": prompt,
            "device_id": device_id,
            "count": count
        }
    )

    return response.json()
```

**JavaScript/Node.js Client**
```javascript
async function generatePlaylist(prompt, deviceId, count = 20) {
    const response = await fetch('http://localhost:8000/generate-playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt,
            device_id: deviceId,
            count: count
        })
    });

    return await response.json();
}
```

### Mobile App Integration

EchoTuner is designed to work seamlessly with mobile applications and will soon include its own dedicated app:

**EchoTuner API:**
- **Playlist Generation**: App calls EchoTuner API for intelligent recommendations
- **Playlist Creation**: App creates actual Spotify playlists using returned song data
- **User Experience**: Smooth handoff between AI recommendations and music playback

**EchoTuner App:**
- Spotify user authentication handling, yet to include
- Native user interface for playlist creation and management
- Direct integration with music streaming services
- Advanced personalization and discovery features
- Simplified setup with automatic dependency management

## Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Verify model availability
ollama pull nomic-embed-text
ollama pull phi3:mini
```

**Spotify API Issues**
- Verify credentials in `.env` file
- Check Spotify Developer Dashboard for API quotas
- Ensure proper redirect URI configuration

**Rate Limiting**
- Check current limits via `/rate-limit-status` endpoint
- Adjust `MAX_PLAYLISTS_PER_DAY` in configuration
- Disable rate limiting for development: `PLAYLIST_LIMIT_ENABLED=false` and `REFINEMENT_LIMIT_ENABLED=false`

### Performance Optimization

**AI Model Performance**
- Use SSD storage for faster model loading
- Increase system RAM for better model caching
- Consider GPU acceleration for larger deployments

**API Performance**
- Enable caching with `CACHE_ENABLED=true`
- Implement connection pooling for database operations
- Use reverse proxy for static content serving

## Contributing

EchoTuner follows standard contribution practices:

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/new-feature`)
3. **Commit** changes (`git commit -am 'Add new feature'`)
4. **Push** to branch (`git push origin feature/new-feature`)
5. **Create** Pull Request

## License

This project is licensed under the Apache 2.0 License - see the `LICENSE` file for details.

## Support

For issues, questions, or contributions:

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Refer to this README and inline code documentation
- **Development**: Follow the contributing guidelines above
