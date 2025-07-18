"""
Security decorators and middleware for production deployment.
Provides endpoint protection and security features for EchoTuner API.
"""

import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class Security:
    def get_security_headers(self, nonce: str = None):
        """Get security headers for production deployment."""

        if settings.SECURE_HEADERS:
            script_src = f"'self' 'nonce-{nonce}'" if nonce else "'self'"

            return {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY", 
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": f"default-src 'self'; style-src 'self'; script-src {script_src}",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            }

        return {}

    def validate_production_readiness(self):
        """Validate that the API is ready for production deployment."""

        issues = []

        if not settings.SPOTIFY_CLIENT_ID:
            issues.append("SPOTIFY_CLIENT_ID not configured")

        if not settings.SPOTIFY_CLIENT_SECRET:
            issues.append("SPOTIFY_CLIENT_SECRET not configured")

        if settings.DEBUG:
            issues.append("DEBUG mode is enabled (should be false in production)")

        if not settings.AUTH_REQUIRED:
            issues.append("AUTH_REQUIRED is disabled (should be true in production)")

        if not settings.SECURE_HEADERS:
            issues.append("SECURE_HEADERS is disabled (should be true in production)")

        if not settings.PLAYLIST_LIMIT_ENABLED:
            issues.append("PLAYLIST_LIMIT_ENABLED is disabled (recommended for production)")

        return issues

security = Security()
