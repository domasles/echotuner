# Security & Rate Limiting

This guide covers EchoTuner's security features and rate limiting configuration.

## Security Headers

EchoTuner automatically applies security headers when `SECURE_HEADERS=true`:

### Default Security Headers

```python
# Applied to all responses
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
}
```

### Custom Security Headers

Modify `services/security.py` to customize headers:

```python
def get_security_headers() -> Dict[str, str]:
    """Get security headers based on configuration."""
    headers = {}
    
    if settings.SECURE_HEADERS:
        headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block", 
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Custom CSP for your domain
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.spotify.com;"
            ),
            
            # Add HSTS for HTTPS deployments
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Prevent MIME type sniffing
            "X-Download-Options": "noopen",
            
            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin"
        })
    
    return headers
```

## CORS Configuration

### Basic CORS Setup

```env
# .env
CORS_ENABLED=true
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Advanced CORS Configuration

Modify `main.py` for custom CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
    max_age=600,  # Cache preflight requests for 10 minutes
)
```

### Environment-Specific CORS

#### Development
```env
CORS_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Production
```env
CORS_ENABLED=true
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

## Authentication & Session Security

### Session Management

```env
# Session configuration
SECRET_KEY=your-256-bit-secret-key-here
MAX_SESSION_AGE=86400                     # 24 hours
SESSION_CLEANUP_INTERVAL=3600             # 1 hour cleanup
AUTH_ATTEMPT_TIMEOUT=300                  # 5 minutes
```

### Secure Session Configuration

Create secure session settings in `config/settings.py`:

```python
class Settings(BaseSettings):
    # Session security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    MAX_SESSION_AGE: int = Field(default=86400, env="MAX_SESSION_AGE")  # 24 hours
    SESSION_CLEANUP_INTERVAL: int = Field(default=3600, env="SESSION_CLEANUP_INTERVAL")
    
    # Authentication security
    AUTH_ATTEMPT_TIMEOUT: int = Field(default=300, env="AUTH_ATTEMPT_TIMEOUT")  # 5 minutes
    MAX_AUTH_ATTEMPTS: int = Field(default=5, env="MAX_AUTH_ATTEMPTS")
    
    # Device registration
    DEVICE_REGISTRATION_TIMEOUT: int = Field(default=1800, env="DEVICE_REGISTRATION_TIMEOUT")  # 30 minutes
    MAX_DEVICES_PER_USER: int = Field(default=10, env="MAX_DEVICES_PER_USER")
```

### Session Cleanup

Implement automatic session cleanup:

```python
# services/auth_service.py
class AuthService:
    async def cleanup_expired_sessions(self):
        """Remove expired sessions and auth attempts."""
        current_time = time.time()
        
        # Remove expired sessions
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session.created_at > settings.MAX_SESSION_AGE
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        
        # Remove expired auth attempts
        expired_attempts = [
            attempt_id for attempt_id, attempt in self.auth_attempts.items()
            if current_time - attempt.created_at > settings.AUTH_ATTEMPT_TIMEOUT
        ]
        
        for attempt_id in expired_attempts:
            del self.auth_attempts[attempt_id]
            logger.debug(f"Cleaned up expired auth attempt: {attempt_id}")
```

## Rate Limiting

### Global Rate Limiting

```env
# Global rate limits
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_WINDOW_SECONDS=60
```

### Endpoint-Specific Rate Limits

Configure different limits for different endpoints:

```python
# services/rate_limiter.py
class RateLimiter:
    def __init__(self):
        self.limits = {
            "playlist_generate": {
                "requests": 10,
                "window": 300,  # 5 minutes
                "scope": "device"
            },
            "playlist_refine": {
                "requests": 20,
                "window": 300,
                "scope": "device"
            },
            "auth_init": {
                "requests": 5,
                "window": 60,
                "scope": "ip"
            },
            "search": {
                "requests": 100,
                "window": 60,
                "scope": "session"
            }
        }
    
    async def check_rate_limit(self, key: str, identifier: str, endpoint: str) -> bool:
        """Check if request is within rate limits."""
        limit_config = self.limits.get(endpoint)
        if not limit_config:
            return True  # No limit configured
        
        # Implementation depends on storage backend
        return await self._check_limit(identifier, limit_config)
```

### Rate Limit Middleware

```python
# utils/rate_limit_middleware.py
from fastapi import Request, HTTPException
from typing import Callable

def rate_limit(requests: int, window: int, scope: str = "ip"):
    """Rate limiting decorator."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Determine identifier based on scope
            if scope == "ip":
                identifier = request.client.host
            elif scope == "session":
                identifier = request.headers.get("X-Device-ID", request.client.host)
            elif scope == "device":
                identifier = request.headers.get("X-Device-ID")
                if not identifier:
                    raise HTTPException(status_code=400, detail="Device ID required")
            else:
                identifier = request.client.host
            
            # Check rate limit
            rate_limiter = request.app.state.rate_limiter
            allowed, retry_after = await rate_limiter.check_rate_limit(
                f"{scope}:{identifier}:{func.__name__}",
                requests,
                window
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)} if retry_after else {}
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Usage in Endpoints

```python
# endpoints/playlists.py
@rate_limit(requests=10, window=300, scope="device")
async def generate_playlist(request: PlaylistRequest):
    """Generate playlist with rate limiting."""
    # Implementation...
```

## Security Best Practices

### Input Validation

```python
# models.py - Use Pydantic for input validation
from pydantic import BaseModel, Field, validator
import re

class PlaylistRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    session_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    device_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('prompt')
    def validate_prompt(cls, v):
        # Remove potentially dangerous content
        if any(keyword in v.lower() for keyword in ['<script', 'javascript:', 'data:']):
            raise ValueError('Invalid prompt content')
        return v.strip()
```

### API Key Security

```python
# Secure API key handling
import secrets
import hashlib

class APIKeyManager:
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return f"ech_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hash_value: str) -> bool:
        """Verify API key against hash."""
        return hashlib.sha256(api_key.encode()).hexdigest() == hash_value
```

### SQL Injection Prevention

```python
# Use SQLAlchemy with parameterized queries
from sqlalchemy import text

# Good - parameterized query
async def get_user_playlists(user_id: str):
    query = text("SELECT * FROM playlists WHERE user_id = :user_id")
    result = await database.fetch_all(query, values={"user_id": user_id})
    return result

# Bad - string interpolation (vulnerable to SQL injection)
# query = f"SELECT * FROM playlists WHERE user_id = '{user_id}'"
```

### Data Sanitization

```python
# utils/sanitization.py
import html
import re
from typing import Optional

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize user input text."""
    if not text:
        return ""
    
    # Limit length
    text = text[:max_length]
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # HTML escape
    text = html.escape(text)
    
    # Remove script tags and javascript
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace('..', '')
    return filename[:255]  # Limit length
```

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

### Environment Variables

```bash
# Never commit these to version control
export SECRET_KEY="$(openssl rand -base64 32)"
export SPOTIFY_CLIENT_SECRET="your-secret-here"
export OPENAI_API_KEY="your-key-here"
```

### Docker Security

```dockerfile
# Dockerfile - security best practices
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/config/health || exit 1

# Start application
CMD ["python", "main.py"]
```

### Reverse Proxy Configuration

#### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    limit_req zone=api burst=10 nodelay;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Next Steps

- Review [Environment Configuration](environment.md) for complete setup
- Check [Custom AI Providers](ai-providers.md) for secure provider implementation
- See [API Quick Start](../quick-start.md) for deployment instructions
