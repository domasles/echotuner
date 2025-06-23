# EchoTuner - AI Powered Playlist Generation Platform

EchoTuner is a production-ready platform that generates personalized music playlists using artificial intelligence and natural language processing. Built with strict dependency requirements, EchoTuner requires both Ollama AI models and Spotify Web API to deliver intelligent music recommendations with zero fallback mechanisms, ensuring consistent AI-driven results.

The platform consists of a RESTful API service for integration with third-party applications, plus a dedicated user application (coming soon) for direct music discovery and playlist creation.

## Project Status

**Current Stage: Production-Ready Platform**

EchoTuner currently consists of a complete, production-ready API backend service designed for integration with music applications, mobile apps, and web platforms. The API provides intelligent playlist generation capabilities while maintaining strict quality standards through required AI and music service dependencies.

**Platform Components:**
- **API Backend**: Complete and production-ready (current release)
- **User Application**: In development, coming soon for direct music discovery
- **Integration Libraries**: Available for third-party development

**Key Characteristics:**
- **Zero-Fallback Architecture**: Requires both Ollama and Spotify API to be operational
- **Pure AI-Driven**: No hardcoded song databases or keyword-based fallbacks
- **Real-Time Processing**: Live Spotify search integrated with local AI analysis
- **Production Hardened**: Comprehensive error handling with graceful failures
- **Integration Ready**: RESTful API designed for both internal app and external integration

## Architecture Overview

### Core Dependencies (Required)

**Ollama Local AI Stack**
- **Validation Model**: `nomic-embed-text` for semantic prompt validation
- **Generation Model**: `phi3:mini` for intelligent playlist strategy generation
- **Local Processing**: All AI operations run on your infrastructure
- **No External AI APIs**: Complete independence from cloud AI services

**Spotify Web API Integration**
- **Real-Time Search**: Live access to Spotify's music catalog
- **Current Music Data**: No static databases, always up-to-date content
- **Authenticated Access**: Requires valid Spotify Developer credentials

### Service Architecture

**FastAPI Backend**
- Asynchronous request processing
- Comprehensive error handling and logging
- Rate limiting and abuse prevention
- Health monitoring and status endpoints

**AI Pipeline**
- **Prompt Validation**: Semantic analysis to ensure music-related requests
- **Strategy Generation**: AI-powered mood and genre analysis
- **Music Search**: Real-time Spotify API integration
- **Result Processing**: Intelligent song selection and playlist assembly

**Application Layer** (Coming Soon)
- Direct user interface for playlist creation
- Advanced playlist management and curation
- Personalized music discovery features
- Seamless integration with popular music streaming services

## Quick Start Guide

**Note**: This guide covers the API backend setup. A dedicated user application is coming soon for direct music discovery without requiring technical setup.

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed from [https://ollama.ai](https://ollama.ai)
3. **Spotify Developer Account** for API credentials

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/domasles/echotuner
   cd echotuner/api
   ```

2. **Configure a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Run automated setup:**
   ```bash
   python setup.py
   ```
   
   This will:
   - Install all Python dependencies
   - Create a `.env` file from the template
   - Provide clear next steps for completing the setup

4. **Complete the setup by following the printed instructions:**
   - Install required AI models:
     ```bash
     ollama pull nomic-embed-text
     ollama pull phi3:mini
     ```
   - Configure Spotify API credentials in the `.env` file (see below)

5. **Configure Spotify API:**
   - Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app and note Client ID and Client Secret
   - Add credentials to `.env` file:
     ```
     SPOTIFY_CLIENT_ID=your_client_id_here
     SPOTIFY_CLIENT_SECRET=your_client_secret_here
     ```

6. **Start the API:**
   ```bash
   python main.py
   ```

The API backend will be available at `http://localhost:8000`

**Coming Soon**: A user-friendly application that will handle all technical setup automatically.

### Verification

**Test API Health:**
```bash
curl http://localhost:8000/health
```

**Generate a playlist:**
```bash
curl -X POST http://localhost:8000/generate-playlist \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "I need upbeat songs for working out",
        "device_id": "my-device",
        "count": 10
    }'
```

## Features

### Core Capabilities
- **Natural Language Processing**: Understands complex mood and preference descriptions
- **AI-Powered Strategy Generation**: Uses local Ollama models for intelligent music analysis
- **Real-Time Music Discovery**: Live integration with Spotify's current catalog
- **Exact Count Control**: Guarantees precise playlist sizes (5-50+ songs)
- **Playlist Refinement**: Iterative improvement based on user feedback
- **Semantic Validation**: Ensures requests are music-related using AI embeddings

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
    "can_refine": true
}
```

#### `GET /health`
Service health and dependency status.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.2.0",
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

## Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Ollama AI Models
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VALIDATION_MODEL=nomic-embed-text
OLLAMA_GENERATION_MODEL=phi3:mini
USE_OLLAMA=true
OLLAMA_TIMEOUT=30

# Spotify Integration
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Rate Limiting
DAILY_LIMIT_ENABLED=true
MAX_PLAYLISTS_PER_DAY=10
MAX_REFINEMENTS_PER_PLAYLIST=3

# Caching
CACHE_ENABLED=true
```

### Rate Limiting Configuration

- **Development**: Set `DAILY_LIMIT_ENABLED=false` for unlimited testing
- **Production**: Enable rate limiting with appropriate daily quotas

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
DAILY_LIMIT_ENABLED=true
MAX_PLAYLISTS_PER_DAY=50
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

**Current Integration (API-based):**
- **Authentication**: App handles Spotify user authentication
- **Playlist Generation**: App calls EchoTuner API for intelligent recommendations
- **Playlist Creation**: App creates actual Spotify playlists using returned song data
- **User Experience**: Smooth handoff between AI recommendations and music playback

**Upcoming EchoTuner App:**
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
- Disable rate limiting for development: `DAILY_LIMIT_ENABLED=false`

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
