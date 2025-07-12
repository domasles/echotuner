# Configuration Endpoints

Configuration endpoints provide system information, **Response:**
```json
{
    "message": "Configuration reloaded successfully",
    "status": "success"
}
```

### GET `/config/production-check` (debug only)

Check if the API is ready for production deployment.

**Response:**
```json
{
    "production_ready": true,
    "issues": [],
    "recommendations": [
        "Set DEBUG=false in production",
        "Enable AUTH_REQUIRED=true",
        "Enable SECURE_HEADERS=true",
        "Configure rate limiting",
        "Use HTTPS in production",
        "Set up proper logging",
        "Configure monitoring"
    ]
}
```

## Error Responsesatus, and administrative functions.

## Public Endpoints

### GET `/`

Get API welcome message and endpoint information.

**Response:**
```json
{
    "message": "Welcome to EchoTuner API",
    "description": "AI-powered playlist generation with real-time song search",
    "demo_mode": false,
    "demo_info": null,
    "endpoints": {
        "generate": "/playlist/generate",
        "refine": "/playlist/refine",
        "update_draft": "/playlist/update-draft",
        "health": "/config/health",
        "rate_limit": "/auth/rate-limit-status",
        "auth_init": "/auth/init",
        "auth_callback": "/auth/callback",
        "auth_validate": "/auth/validate",
        "library": "/playlist/library",
        "add_to_spotify": "/spotify/create-playlist",
        "get_draft": "/playlist/drafts"
    }
}
```

### GET `/config`

Get client configuration values and API information.

**Response:**
```json
{
    "personality": {
        "max_favorite_artists": 10,
        "max_disliked_artists": 5,
        "max_favorite_genres": 8,
        "max_preferred_decades": 4
    },
    "playlists": {
        "max_songs_per_playlist": 50,
        "max_playlists_per_day": 5,
        "max_refinements_per_playlist": 3
    },
    "features": {
        "auth_required": true,
        "playlist_limit_enabled": true,
        "refinement_limit_enabled": true
    },
    "demo_mode": false
}
```

### GET `/config/health`

Check API health and service status.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.1.0-beta",
    "features": {
        "rate_limiting": true
    }
}
```

## Debug Endpoints

### POST `/config/reload` (debug only)

Reload JSON configuration files without restarting the server.

**Response:**
```json
{
    "message": "Configuration reloaded successfully",
    "status": "success"
}
```

**Error Response:**
```json
{
    "detail": "Failed to reload configuration: Invalid JSON syntax at line 15"
}
```

### GET `/config/production-check` (debug only)

Check if the API is ready for production deployment.

**Response:**
```json
{
    "production_ready": true,
    "issues": [],
    "recommendations": [
        "Set DEBUG=false in production",
        "Enable AUTH_REQUIRED=true",
        "Enable SECURE_HEADERS=true",
        "Configure rate limiting",
        "Use HTTPS in production",
        "Set up proper logging",
        "Configure monitoring"
    ]
}
```

## Server Information

### GET `/server/mode`

Get current server mode and configuration.

**Response:**
```json
{
    "demo_mode": false,
    "mode": "normal|demo",
}
```

## Configuration Values

The `/config` endpoint provides essential configuration for client applications:

### Endpoint Mapping

The `endpoints` object maps logical endpoint names to actual API paths:

- `generate`: Playlist generation endpoint
- `refine`: Playlist refinement endpoint  
- `update_draft`: Draft update endpoint
- `health`: Health check endpoint
- `rate_limit`: Rate limit status endpoint
- Authentication endpoints (`auth_init`, `auth_callback`, `auth_validate`)
- Spotify integration endpoints
- Library and draft management endpoints

### Demo Mode

When `demo_mode` is true:
- Users share a common Spotify account
- Rate limits are shared across all users
- Some features may be restricted
- `demo_info` provides explanation text

## Error Handling

### Health Check Failures

Health checks in debug mode only return basic status:

```json
{
    "status": "healthy",
    "version": "1.1.0-beta",
    "features": {
        "rate_limiting": true
    }
}
```

Or an HTTP 403 error in production mode:

```json
{
    "detail": "API health check is disabled in production mode"
}
```

### Configuration Reload Errors

If configuration reload fails:

```json
{
    "detail": "Failed to reload configuration: Invalid JSON syntax at line 15"
}
```

## Error Responses

Configuration endpoints may return these error responses:

- `403 Forbidden`: Health check disabled in production mode
- `500 Internal Server Error`: Failed to reload configuration

**Error Format:**
```json
{
    "detail": "string"
}
```

### Production Readiness

The production check verifies:
- Security configuration
- Performance settings
- External service connectivity
- Resource availability
- Configuration completeness

Use this endpoint in CI/CD pipelines to ensure safe deployments.
