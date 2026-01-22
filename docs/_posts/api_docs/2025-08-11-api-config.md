---
title: Configuration & Health API
date: 2025-08-11 14:30:00 +0000
categories: [API Documentation, Configuration]
tags: [api, config, health, settings, limits]
---

# Configuration & Health API

The Configuration API provides information about system settings, feature flags, health status, and operational limits. This API helps clients understand available features and configure themselves appropriately.

## Base Path: `/config`

## Endpoints

### Health Check

```http
GET /config/health
```

Check the overall health and status of the EchoTuner API.

#### Response

```json
{
  "status": "healthy",
  "version": "2.1.2-beta"
}
```

#### Example

```bash
curl -X GET "https://echotuner-api.domax.lt/config/health"
```

---

### Get Configuration

```http
GET /config
```

Retrieve client configuration settings, limits, and feature flags.

#### Response

```json
{
  "personality": {
    "max_favorite_artists": 50,
    "max_disliked_artists": 25,
    "max_favorite_genres": 20,
    "max_preferred_decades": 10
  },
  "playlists": {
    "max_songs_per_playlist": 50,
    "max_playlists_per_day": 10,
    "max_prompt_length": 500,
    "max_playlist_name_length": 100
  },
  "features": {
    "auth_required": true,
    "playlist_limit_enabled": true,
    "spotify_integration_enabled": true,
    "google_auth_enabled": true,
    "shared_mode_available": true
  },
  "supported_providers": [
    "spotify",
    "google"
  ],
  "api_version": "2.1.2-beta",
  "server_mode": "shared"
}
```

#### Example

```bash
curl -X GET "https://echotuner-api.domax.lt/config"
```

---

### Get Available Genres

```http
GET /config/genres
```

Retrieve list of supported music genres for personality preferences.

#### Response

```json
{
  "genres": [
    "pop",
    "rock",
    "hip-hop",
    "electronic",
    "jazz",
    "classical",
    "country",
    "r&b",
    "indie",
    "alternative",
    "folk",
    "blues",
    "reggae",
    "punk",
    "metal"
  ],
  "total_count": 150,
  "last_updated": "2025-08-01T00:00:00Z"
}
```

---

### Get Supported Decades

```http
GET /config/decades
```

Get list of supported decade preferences.

#### Response

```json
{
  "decades": [
    "1960s",
    "1970s",
    "1980s",
    "1990s",
    "2000s",
    "2010s",
    "2020s"
  ],
  "current_decade": "2020s"
}
```

---

### Get Discovery Strategies

```http
GET /config/discovery-strategies
```

List available playlist discovery strategies and their descriptions.

#### Response

```json
{
  "strategies": [
    {
      "id": "balanced",
      "name": "Balanced",
      "description": "Mix of familiar and new music with moderate exploration",
      "default": true
    },
    {
      "id": "exploration",
      "name": "Exploration",
      "description": "Focus on discovering new music and artists",
      "default": false
    },
    {
      "id": "conservative",
      "name": "Conservative",
      "description": "Stick closely to known preferences with minimal exploration",
      "default": false
    }
  ]
}
```

## Base Path: `/server`

### Get Server Mode

```http
GET /server/mode
```

Determine the current server operational mode.

#### Response

```json
{
  "shared_mode": true,
  "mode": "shared",
  "description": "Server is running in shared mode with Google authentication",
  "features": {
    "individual_spotify_auth": false,
    "google_auth_required": true,
    "shared_spotify_account": true
  }
}
```

#### Example

```bash
curl -X GET "https://echotuner-api.domax.lt/server/mode"
```

## Base Path: `/ai`

### Get AI Models

```http
GET /ai/models
```

List available AI models and their configurations.

#### Response

```json
{
  "available_models": {
    "openai-gpt4": {
      "name": "OpenAI GPT-4",
      "provider": "openai",
      "status": "available",
      "capabilities": ["text-generation", "music-analysis"],
      "rate_limit": 100
    },
    "anthropic-claude": {
      "name": "Anthropic Claude",
      "provider": "anthropic",
      "status": "available",
      "capabilities": ["text-generation", "reasoning"],
      "rate_limit": 50
    },
    "local-model": {
      "name": "Local Model",
      "provider": "local",
      "status": "offline",
      "error": "Model not loaded"
    }
  },
  "default_model": "openai-gpt4",
  "total_available": 2
}
```

---

### Test AI Model (Debug Only)

```http
POST /ai/test
```

Test AI model functionality with a simple prompt (development/debug environments only).

#### Request Body

```json
{
  "model_id": "openai-gpt4",
  "prompt": "Generate a short music recommendation"
}
```

#### Response

```json
{
  "model_used": {
    "name": "OpenAI GPT-4",
    "provider": "openai"
  },
  "response": "I recommend checking out some ambient electronic music...",
  "execution_time": 1.2
}
```

> **Note**: This endpoint is only available in debug/development mode
{: .prompt-warning }

## Configuration Fields

### Personality Limits

| Field | Description | Default |
|-------|-------------|---------|
| `max_favorite_artists` | Maximum favorite artists per user | 50 |
| `max_disliked_artists` | Maximum disliked artists per user | 25 |
| `max_favorite_genres` | Maximum favorite genres per user | 20 |
| `max_preferred_decades` | Maximum decade preferences per user | 10 |

### Playlist Limits

| Field | Description | Default |
|-------|-------------|---------|
| `max_songs_per_playlist` | Songs per generated playlist | 50 |
| `max_playlists_per_day` | Daily playlist generation limit | 10 |
| `max_prompt_length` | Maximum prompt text length | 500 |
| `max_playlist_name_length` | Maximum Spotify playlist name | 100 |

### Feature Flags

| Field | Description | Impact |
|-------|-------------|--------|
| `auth_required` | Whether authentication is required | Endpoint access |
| `playlist_limit_enabled` | Whether rate limiting is active | Daily usage limits |
| `spotify_integration_enabled` | Spotify playlist creation available | Spotify endpoints |
| `google_auth_enabled` | Google OAuth available | Authentication options |
| `shared_mode_available` | Shared mode functionality | Server behavior |

## Server Modes

### Normal Mode
```json
{
  "shared_mode": false,
  "mode": "normal",
  "features": {
    "individual_spotify_auth": true,
    "google_auth_required": false,
    "shared_spotify_account": false
  }
}
```

### Shared Mode
```json
{
  "shared_mode": true,
  "mode": "shared",
  "features": {
    "individual_spotify_auth": false,
    "google_auth_required": true,
    "shared_spotify_account": true
  }
}
```

## Error Handling

### Common Errors

#### 503 Service Unavailable - Unhealthy Service
```json
{
  "status": "unhealthy",
  "error": "Database connection failed",
  "services": {
    "database": "unhealthy",
    "spotify_api": "healthy"
  }
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to retrieve configuration"
}
```

## Usage Examples

### Client Initialization

```javascript
class EchoTunerClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.config = null;
  }

  async initialize() {
    // Get configuration
    const configResponse = await fetch(`${this.baseUrl}/config`);
    this.config = await configResponse.json();

    // Check health
    const healthResponse = await fetch(`${this.baseUrl}/config/health`);
    const health = await healthResponse.json();

    if (health.status !== 'healthy') {
      throw new Error('Service is currently unavailable');
    }

    // Get server mode
    const modeResponse = await fetch(`${this.baseUrl}/server/mode`);
    this.serverMode = await modeResponse.json();

    return {
      config: this.config,
      health: health,
      mode: this.serverMode
    };
  }

  getPlaylistLimits() {
    return this.config?.playlists || {};
  }

  getPersonalityLimits() {
    return this.config?.personality || {};
  }

  isFeatureEnabled(feature) {
    return this.config?.features?.[feature] || false;
  }

  isSharedMode() {
    return this.serverMode?.shared_mode || false;
  }
}

// Usage
const client = new EchoTunerClient('https://echotuner-api.domax.lt');
await client.initialize();

console.log('Max playlists per day:', client.getPlaylistLimits().max_playlists_per_day);
console.log('Auth required:', client.isFeatureEnabled('auth_required'));
console.log('Running in shared mode:', client.isSharedMode());
```

### Dynamic UI Configuration

```javascript
const configureUI = async () => {
  const configResponse = await fetch('/config');
  const config = await configResponse.json();

  // Configure form limits
  document.getElementById('prompt-input').setAttribute(
    'maxlength', 
    config.playlists.max_prompt_length
  );

  // Show/hide features based on flags
  if (!config.features.spotify_integration_enabled) {
    document.getElementById('spotify-section').style.display = 'none';
  }

  // Configure rate limit display
  document.getElementById('daily-limit').textContent = 
    `${config.playlists.max_playlists_per_day} playlists per day`;

  // Configure personality limits
  const artistLimit = config.personality.max_favorite_artists;
  document.getElementById('artist-limit').textContent = 
    `Add up to ${artistLimit} favorite artists`;
};
```

### Health Monitoring

```javascript
const monitorHealth = async () => {
  try {
    const response = await fetch('/config/health');
    const health = await response.json();

    if (health.status === 'healthy') {
      console.log('All services operational');
    } else {
      console.warn('Some services degraded:', health.services);
    }

    // Check specific services
    Object.entries(health.services).forEach(([service, status]) => {
      if (status !== 'healthy') {
        console.error(`${service} is ${status}`);
      }
    });

  } catch (error) {
    console.error('Health check failed:', error);
  }
};

// Monitor every 30 seconds
setInterval(monitorHealth, 30000);
```

## Next Steps

- **[Authentication API](/posts/api-authentication/)** - Set up user authentication
- **[Playlist Generation API](/posts/api-playlists/)** - Use configuration limits for playlist creation
- **[User Management API](/posts/api-users/)** - Check rate limiting status
