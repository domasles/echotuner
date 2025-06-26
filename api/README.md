# EchoTuner API - AI-Powered Playlist Generation Backend

The EchoTuner API is a production-ready RESTful service that generates personalized music playlists using artificial intelligence and natural language processing. This backend service powers the EchoTuner platform with intelligent music recommendations through strict dependency requirements and zero-fallback architecture.

## Overview

The API provides intelligent playlist generation capabilities while maintaining strict quality standards through required AI and music service dependencies. Built with FastAPI, it offers asynchronous request processing, comprehensive error handling, and seamless integration capabilities for third-party applications.

**Key Features:**
- **Pure AI-Driven**: No hardcoded song databases or keyword-based fallbacks
- **Real-Time Processing**: Live Spotify search integrated with local AI analysis
- **Zero-Fallback Architecture**: Requires both Ollama and Spotify API to be operational
- **Production Hardened**: Comprehensive error handling with graceful failures
- **Integration Ready**: RESTful API designed for both internal app and external integration
- **Configurable Rate Limiting**: Independent playlist and refinement limits with backend control

## Core Dependencies

**Ollama Local AI Stack (Required)**
- **Validation Model**: `nomic-embed-text` for semantic prompt validation
- **Generation Model**: `phi3:mini` for intelligent playlist strategy generation
- **Local Processing**: All AI operations run on your infrastructure
- **No External AI APIs**: Complete independence from cloud AI services

**Spotify Web API Integration (Required)**
- **Real-Time Search**: Live access to Spotify's music catalog
- **Current Music Data**: No static databases, always up-to-date content
- **Authenticated Access**: Requires valid Spotify Developer credentials

## Quick Start

For complete installation and setup instructions, please refer to the [master installation guide](../README.md#installation) in the project root.

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed from [https://ollama.ai](https://ollama.ai)
3. **Spotify Developer Account** for API credentials
4. **Spotify API credentials** (Client ID and Client Secret)

### Installaton

1. **Navigate to API directory:**
   ```bash
   cd echotuner/api
   ```

2. **Copy over .env.sample to .env:**
    ```bash
    cp .env.sample .env
    ```
    Don't forget to Configure Spotify API credentials in the generated `.env` file

3. **Run automated setup:**
   ```bash
   python setup.py
   ```

4. **Install required AI models:**
   ```bash
   ollama pull nomic-embed-text
   ollama pull phi3:mini
   ```

5. **Start the API:**
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

### Health Monitoring

```bash
# Check API health
curl http://localhost:8000/health

# Test playlist generation
curl -X POST http://localhost:8000/generate-playlist \
    -H "Content-Type: application/json" \
    -d '{"prompt":"relaxing jazz for studying","device_id":"test","count":10}'
```

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
