# Environment Configuration

This guide covers how to configure EchoTuner's environment variables and settings.

## Environment File Structure

EchoTuner uses a `.env` file for configuration. Create this file in the `api/` directory by copying `.env.sample`:

```bash
cp .env.sample .env
```

Here's the complete configuration structure based on the actual project:

```env
# Core Application Settings
API_HOST=0.0.0.0
API_PORT=8000
DEMO=false
DEBUG=true
LOG_LEVEL=INFO
DATABASE_FILENAME=echotuner.db

# AI Configuration
AI_PROVIDER=ollama
AI_ENDPOINT=http://localhost:11434
AI_GENERATION_MODEL=phi3:mini
AI_EMBEDDING_MODEL=nomic-embed-text:latest
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_TIMEOUT=30
AI_MODEL_PULL_TIMEOUT=300

# Cloud AI Configuration (Optional)
CLOUD_API_KEY=your-cloud-ai-api-key-here

# Prompt Validation
PROMPT_VALIDATION_THRESHOLD=0.6
PROMPT_VALIDATION_TIMEOUT=30

# Spotify Integration
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri_here

# Authentication
AUTH_REQUIRED=true

# Rate Limiting
PLAYLIST_LIMIT_ENABLED=false
REFINEMENT_LIMIT_ENABLED=false
MAX_PLAYLISTS_PER_DAY=3
MAX_SONGS_PER_PLAYLIST=30
MAX_REFINEMENTS_PER_PLAYLIST=3

# Sessions and Storage
SESSION_TIMEOUT=24
DRAFT_STORAGE_TIMEOUT=7
DRAFT_CLEANUP_INTERVAL=24

# Cache Settings
CACHE_ENABLED=true

# User Limits
MAX_FAVORITE_ARTISTS=12
MAX_DISLIKED_ARTISTS=20
MAX_FAVORITE_GENRES=10
MAX_PREFERRED_DECADES=5

# Security
MAX_AUTH_ATTEMPTS_PER_IP=10
AUTH_ATTEMPT_WINDOW_MINUTES=60
SECURE_HEADERS=true

# Input Validation
MAX_PROMPT_LENGTH=128
MAX_PLAYLIST_NAME_LENGTH=100
```

## Configuration Categories

### Core Application

```env
# Development vs Production
DEBUG=true                    # Enable debug mode and debug endpoints
API_HOST=0.0.0.0             # API server host (0.0.0.0 for all interfaces)
API_PORT=8000                # API server port
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)
```

**Production Values:**
```env
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=WARNING
```

### Security Configuration

```env
# Security Headers and CORS
SECRET_KEY=your-256-bit-secret-key              # Used for session signing
SECURE_HEADERS=true                             # Enable security headers
CORS_ENABLED=true                               # Enable CORS middleware
ALLOWED_ORIGINS=https://yourapp.com,https://app.yourapp.com  # CORS origins
```

**Security Key Generation:**
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Spotify Integration

```env
# Spotify App Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback

# Spotify API Settings
SPOTIFY_SCOPE=playlist-modify-public,playlist-modify-private,user-follow-read,user-library-read
SPOTIFY_MARKET=US                               # Default market for search results
```

**Setup Instructions:**
1. Create a Spotify app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Add redirect URI to your app settings
3. Copy Client ID and Client Secret to your `.env` file

### AI Provider Configuration

The project supports multiple AI providers. Choose one by setting `AI_PROVIDER`:

#### Ollama (Default - Local AI)
```env
AI_PROVIDER=ollama
AI_ENDPOINT=http://localhost:11434
AI_GENERATION_MODEL=phi3:mini
AI_EMBEDDING_MODEL=nomic-embed-text:latest
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_TIMEOUT=30
AI_MODEL_PULL_TIMEOUT=300
```

#### OpenAI
```env
AI_PROVIDER=openai
CLOUD_API_KEY=sk-your-openai-api-key
AI_GENERATION_MODEL=gpt-4
AI_EMBEDDING_MODEL=text-embedding-ada-002
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
```

#### Google AI
```env
AI_PROVIDER=google
CLOUD_API_KEY=your-google-ai-api-key
AI_GENERATION_MODEL=gemini-pro
AI_EMBEDDING_MODEL=embedding-001
AI_MAX_TOKENS=2048
AI_TEMPERATURE=0.7
```

### Database Configuration

EchoTuner uses SQLite by default:

```env
DATABASE_FILENAME=echotuner.db
```

The database file will be created in the API directory.

### Rate Limiting & Quotas

```env
# Playlist Generation Limits
PLAYLIST_LIMIT_ENABLED=true                     # Enable rate limiting
MAX_REFINEMENTS_PER_PLAYLIST=5                  # Max refinements per playlist
RATE_LIMIT_REQUESTS_PER_MINUTE=60              # Global rate limit
RATE_LIMIT_WINDOW_SECONDS=60                   # Rate limit window

# Demo Mode
DEMO_MODE_ENABLED=false                         # Enable demo mode
DEMO_MAX_PLAYLISTS=3                           # Max playlists in demo mode
DEMO_MAX_REFINEMENTS=2                         # Max refinements in demo mode
```

### Session Management

```env
# Session Configuration
SESSION_CLEANUP_INTERVAL=3600                   # Cleanup interval (seconds)
MAX_SESSION_AGE=86400                          # Max session age (24 hours)
AUTH_ATTEMPT_TIMEOUT=300                       # Auth attempt timeout (5 minutes)
DEVICE_REGISTRATION_TIMEOUT=1800               # Device registration timeout
```

## Environment-Specific Configurations

### Development Environment

```env
# Development .env
DEBUG=true
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000
DEMO=true

# Use local Ollama for development
AI_PROVIDER=ollama
AI_ENDPOINT=http://localhost:11434
AI_GENERATION_MODEL=phi3:mini

# Relaxed rate limiting
PLAYLIST_LIMIT_ENABLED=false
REFINEMENT_LIMIT_ENABLED=false
AUTH_REQUIRED=false

# Development Spotify (optional)
SPOTIFY_CLIENT_ID=your_dev_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_dev_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback
```

### Production Environment

```env
# Production .env
DEBUG=false
LOG_LEVEL=WARNING
API_HOST=0.0.0.0
API_PORT=8000
DEMO=false

# Production AI provider
AI_PROVIDER=openai
CLOUD_API_KEY=your_production_openai_key

# Production Spotify
SPOTIFY_CLIENT_ID=your_production_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_production_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://yourdomain.com/auth/callback

# Production rate limiting
PLAYLIST_LIMIT_ENABLED=true
REFINEMENT_LIMIT_ENABLED=true
MAX_PLAYLISTS_PER_DAY=10
MAX_REFINEMENTS_PER_PLAYLIST=3
AUTH_REQUIRED=true

# Security
SECURE_HEADERS=true
```

### Docker Environment

```env
# Docker .env
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=sqlite:///./data/echotuner.db

# Use host network for Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Docker-specific paths
STATIC_FILES_DIR=/app/static
UPLOAD_DIR=/app/uploads
```

## Configuration Validation

The API automatically validates required configuration on startup:

### Required Settings

These settings must be configured for the API to start:

```env
# Always required
SECRET_KEY=your-secret-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret

# Required based on AI_PROVIDER setting
OPENAI_API_KEY=required-if-ai-provider-is-openai
CLOUD_API_KEY=required-if-ai-provider-is-openai-or-google
```

### Optional Settings

These have sensible defaults but can be customized:

```env
DEBUG=false                                     # Default: false
LOG_LEVEL=INFO                                  # Default: INFO
API_HOST=127.0.0.1                             # Default: 127.0.0.1
API_PORT=8000                                   # Default: 8000
```

## Advanced Configuration

### Custom Settings

Add custom settings to `config/settings.py`:

```python
class Settings(BaseSettings):
    # Custom feature flags
    ENABLE_EXPERIMENTAL_FEATURES: bool = Field(default=False, env="ENABLE_EXPERIMENTAL_FEATURES")
    
    # Custom rate limits
    PREMIUM_USER_RATE_LIMIT: int = Field(default=120, env="PREMIUM_USER_RATE_LIMIT")
    
    # Custom AI settings
    AI_RETRY_ATTEMPTS: int = Field(default=3, env="AI_RETRY_ATTEMPTS")
    AI_TIMEOUT_SECONDS: int = Field(default=30, env="AI_TIMEOUT_SECONDS")
```

### Environment Variable Precedence

Configuration is loaded in this order (later values override earlier ones):

1. Default values in `settings.py`
2. Environment variables
3. `.env` file values
4. Runtime configuration (if any)

### Configuration Templates

#### Local Development Template

```bash
cp .env.example .env.local
# Edit .env.local with your local settings
```

#### Production Template

```bash
cp .env.example .env.production
# Edit .env.production with your production settings
```

#### Docker Compose Template

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - DATABASE_URL=postgresql://user:pass@db:5432/echotuner
    env_file:
      - .env.docker
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=echotuner
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## Troubleshooting

### Configuration Errors

#### Missing Required Settings

```bash
ERROR: Configuration validation failed:
  - SPOTIFY_CLIENT_ID is required
  - AI provider 'openai' requires OPENAI_API_KEY
```

**Solution:** Add the missing environment variables to your `.env` file.

#### Invalid Values

```bash
ERROR: Invalid LOG_LEVEL 'VERBOSE'. Must be one of: DEBUG, INFO, WARNING, ERROR
```

**Solution:** Use valid values as documented.

### Environment File Issues

#### File Not Found
```bash
WARNING: .env file not found, using environment variables only
```

**Solution:** Create a `.env` file in the `api/` directory.

#### Permission Issues
```bash
ERROR: Cannot read .env file: Permission denied
```

**Solution:** Check file permissions:
```bash
chmod 644 .env
```

### AI Provider Issues

#### Invalid API Keys
```bash
ERROR: OpenAI API key validation failed
```

**Solution:** Verify your API key is correct and has the necessary permissions.

#### Model Not Available
```bash
WARNING: Model 'gpt-5' not available, using default 'gpt-4'
```

**Solution:** Use a valid model name for your provider.

## Next Steps

- Review [Security Configuration](security.md) for security best practices
- Check [Custom AI Providers](ai-providers.md) for adding new AI providers
- See [API Quick Start](../quick-start.md) for deployment instructions
