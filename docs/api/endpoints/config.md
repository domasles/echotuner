# Configuration Endpoints

Configuration endpoints provide system information, health status, and administrative functions.

## Public Endpoints

### GET `/config`

Get client configuration values and API information.

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

### GET `/config/health`

Check API health and service status.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0-beta",
    "services": {
        "database": "healthy",
        "ai_provider": "healthy",
        "spotify": "healthy"
    },
    "system": {
        "uptime": "2d 5h 30m",
        "memory_usage": "45%",
        "cpu_usage": "12%"
    }
}
```

## Debug Endpoints

### POST `/config/reload` (debug only)

Reload JSON configuration files without restarting the server.

**Response:**
```json
{
    "success": true,
    "reloaded_files": [
        "ai_patterns.json",
        "energy_terms.json",
        "prompt_references.json"
    ],
    "timestamp": "2024-01-01T00:00:00Z"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Failed to reload ai_patterns.json",
    "details": "Invalid JSON syntax at line 15"
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

Health checks may return degraded status:

```json
{
    "status": "degraded",
    "services": {
        "database": "healthy",
        "ai_provider": "unhealthy",
        "spotify": "healthy"
    },
    "errors": {
        "ai_provider": "Connection timeout to Ollama service"
    }
}
```

### Configuration Reload Errors

If configuration reload fails, the API continues with existing configuration:

```json
{
    "success": false,
    "error": "Partial reload failure",
    "reloaded_files": ["energy_terms.json"],
    "failed_files": {
        "ai_patterns.json": "Invalid JSON syntax"
    }
}
```

## Monitoring

### Health Check Usage

The health endpoint is designed for:
- Load balancer health checks
- Monitoring system integration
- Service discovery
- Automated deployment verification

### Production Readiness

The production check verifies:
- Security configuration
- Performance settings
- External service connectivity
- Resource availability
- Configuration completeness

Use this endpoint in CI/CD pipelines to ensure safe deployments.
