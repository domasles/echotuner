# API Quick Start Guide

This guide will help you get the EchoTuner API running locally or with Docker.

## Local Development Setup

### Prerequisites

- **Python 3.8+** with **pip** (for API development)
- **Ollama** (for local AI models) or **Cloud AI** API keys
- **Docker** (optional, for deployment)

### Installation

1. **Navigate to API directory**
    ```bash
    cd api
    ```

2. **Configure environment**
    ```bash
    cp .env.example .env
    # Edit .env file with your settings
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Start the API**
    ```bash
    python main.py
    ```

### Docker Deployment

EchoTuner provides two deployment options for the web app:

### Option 1: Pre-built Images (Recommended)

Uses pre-built images from GitHub Container Registry:

```bash
docker compose up -d
```

### Option 2: Local Build

Build the containers locally:

```bash
# To use local builds instead, use docker compose up --build.
docker compose up --build
```

**Note**: The default docker-compose.yml uses pre-built GHCR images. Docker deployment serves both the Flutter web app and the API, and is recommended for production environments.

## Configuration

### Required Environment Variables

```env
# AI Configuration
AI_PROVIDER=ollama                    # ollama, openai, google
AI_ENDPOINT=http://localhost:11434    # Ollama endpoint or cloud API URL
AI_GENERATION_MODEL=phi3:mini         # Model name for text generation
AI_EMBEDDING_MODEL=nomic-embed-text:latest  # Model for embeddings

# Spotify Integration
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Optional: Cloud AI (if not using Ollama)
CLOUD_API_KEY=your_api_key           # OpenAI or Google API key
```

### Ollama Setup (Local AI)

1. **Install Ollama**
    ```bash
    # macOS/Linux
    curl -fsSL https://ollama.ai/install.sh | sh

    # Windows: Download from https://ollama.ai
    ```

2. **Pull required models**
    ```bash
    ollama pull phi3:mini                    # Generation model
    ollama pull nomic-embed-text:latest      # Embedding model
    ```

3. **Start Ollama service**
    ```bash
    ollama serve
    ```

## Testing the API

1. **Health Check**
    ```bash
    curl http://localhost:8000/config/health
    ```

2. **Get Configuration**
    ```bash
    curl http://localhost:8000/config
    ```

3. **Test AI (debug only)**
    ```bash
    curl -X POST http://localhost:8000/ai/test -H "Content-Type: application/json" -d '{"prompt": "Hello, world!"}'
    ```

## Debug Mode

Enable debug mode for additional endpoints and features:

```env
DEBUG=true
```

Debug endpoints include:
- `/ai/models` - View available AI models
- `/ai/test` - Test AI generation
- `/config/reload` - Reload configuration
- `/config/production-check` - Production readiness check
- `/auth/cleanup` - Clean up expired sessions

## Production Deployment

For production deployment:

1. Set `DEBUG=false`
2. Configure proper security headers
3. Use environment-specific `.env` files
4. Set up proper logging and monitoring
5. Use a reverse proxy (nginx) for SSL termination

## Troubleshooting

### Common Issues

1. **AI Provider Connection Failed**
    - Check if Ollama is running: `ollama list`
    - Verify API endpoints and credentials
    - Check firewall settings

2. **Spotify Authentication Issues**
    - Verify client ID and secret
    - Check redirect URI configuration
    - Ensure app is properly registered with Spotify

3. **Database Issues**
    - Check file permissions for `echotuner.db`
    - Verify SQLite installation

### Logs

Check the API logs for detailed error information:
```bash
# Development
python main.py

# Docker
docker-compose logs api
```
