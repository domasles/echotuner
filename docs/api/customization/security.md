# Security & Rate Limiting

This guide covers EchoTuner's actually implemented security features and rate limiting configuration.

## Security Headers

EchoTuner automatically applies security headers when `SECURE_HEADERS=true` in your `.env` file:

```env
SECURE_HEADERS=true
```

### Available Security Headers

The following headers are applied by the `get_security_headers()` function in `services/security.py`:

```python
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## Rate Limiting

EchoTuner has a built-in rate limiting system for playlist generation requests.

### Configuration

```env
# Rate limiting
PLAYLIST_LIMIT_ENABLED=true
MAX_PLAYLISTS_PER_DAY=3
MAX_REFINEMENTS_PER_PLAYLIST=3
```

### How It Works

- Rate limiting is implemented in `services/rate_limiter.py`
- Tracks requests per device using hashed device IDs
- Enforces daily limits on playlist generation
- Allows configurable refinement limits per playlist

### Rate Limit Status

Check current rate limit status via the `/auth/rate-limit-status` endpoint.

## Production Security

### Security Validation

The `validate_production_readiness()` function in `services/security.py` checks:

- Spotify credentials are configured
- DEBUG mode is disabled
- AUTH_REQUIRED is enabled
- SECURE_HEADERS is enabled
- PLAYLIST_LIMIT_ENABLED is enabled

### Debug-Only Endpoints

The following endpoints are only available when `DEBUG=true`:

- `/config/health` - API health check
- `/ai/models` - AI model status
- `/ai/test` - AI model testing
- `/config/reload` - Configuration reload

## Session Security

### Session Management

Sessions are managed in `services/auth_service.py`:

- Session cleanup removes expired sessions
- Demo sessions are handled separately
- Device-specific authentication state

### Environment Variables

```env
AUTH_REQUIRED=true
SECRET_KEY=your-secret-key-here
DEMO=false
```

## Database Security

The database service includes cleanup methods for:

- Expired authentication attempts
- Expired sessions
- Demo user data
- Rate limit records

These run automatically to maintain database hygiene.

## Best Practices

1. **Always enable security headers in production**: `SECURE_HEADERS=true`
2. **Disable debug mode in production**: `DEBUG=false`
3. **Require authentication in production**: `AUTH_REQUIRED=true`
4. **Enable rate limiting**: `PLAYLIST_LIMIT_ENABLED=true`
5. **Use HTTPS in production** for the Strict-Transport-Security header
6. **Set appropriate CORS origins** instead of using wildcards

## Monitoring & Logging

### Security Event Logging

```python
# services/security_logger.py
import logging
from typing import Dict, Any
from fastapi import Request

security_logger = logging.getLogger("security")

class SecurityLogger:
    @staticmethod
    def log_auth_attempt(request: Request, success: bool, user_id: Optional[str] = None):
        """Log authentication attempts."""
        security_logger.info(
            "Auth attempt",
            extra={
                "event": "auth_attempt",
                "success": success,
                "user_id": user_id,
                "ip": request.client.host,
                "user_agent": request.headers.get("User-Agent"),
                "timestamp": time.time()
            }
        )
    
    @staticmethod
    def log_rate_limit_exceeded(request: Request, endpoint: str):
        """Log rate limit violations."""
        security_logger.warning(
            "Rate limit exceeded",
            extra={
                "event": "rate_limit_exceeded", 
                "endpoint": endpoint,
                "ip": request.client.host,
                "device_id": request.headers.get("X-Device-ID"),
                "timestamp": time.time()
            }
        )
    
    @staticmethod
    def log_suspicious_activity(request: Request, reason: str, details: Dict[str, Any]):
        """Log suspicious activities."""
        security_logger.error(
            f"Suspicious activity: {reason}",
            extra={
                "event": "suspicious_activity",
                "reason": reason,
                "details": details,
                "ip": request.client.host,
                "timestamp": time.time()
            }
        )
```

### Rate Limit Monitoring

```python
# Monitor rate limit usage
class RateLimitMonitor:
    def __init__(self):
        self.usage_stats = {}
    
    async def record_request(self, identifier: str, endpoint: str):
        """Record request for monitoring."""
        key = f"{identifier}:{endpoint}"
        if key not in self.usage_stats:
            self.usage_stats[key] = {"count": 0, "last_request": time.time()}
        
        self.usage_stats[key]["count"] += 1
        self.usage_stats[key]["last_request"] = time.time()
    
    def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get users with highest request counts."""
        sorted_users = sorted(
            self.usage_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        return [
            {"identifier": k, "requests": v["count"], "last_request": v["last_request"]}
            for k, v in sorted_users[:limit]
        ]
```

## Deployment Security


