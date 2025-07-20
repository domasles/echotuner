"""
IP Rate Limiter Service.
IP-based rate limiter service for authentication and security.
"""

import hashlib
import logging

from datetime import datetime, timedelta

from application.core.singleton import SingletonServiceBase

from infrastructure.database.service import db_service
from infrastructure.config.settings import settings

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class IPRateLimiterService(SingletonServiceBase):
    """Service to handle IP-based rate limiting for authentication attempts."""

    def _setup_service(self):
        """Initialize the IP rate limiter service."""

        self.max_attempts = settings.MAX_AUTH_ATTEMPTS_PER_IP
        self.window_minutes = settings.AUTH_ATTEMPT_WINDOW_MINUTES

        self._log_initialization("IP rate limiter service initialized successfully", logger)

    def __init__(self):
        super().__init__()

    def _get_ip_hash(self, ip_address: str) -> str:
        """Create a hash of the IP address for privacy."""

        return hashlib.sha256(ip_address.encode()).hexdigest()

    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is currently blocked due to too many attempts."""

        try:
            validated_ip = UniversalValidator.validate_ip_address(ip_address)
            ip_hash = self._get_ip_hash(validated_ip)

            current_time = datetime.now()
            window_start = current_time - timedelta(minutes=self.window_minutes)

            attempts_count = await db_service.get_ip_attempts_count(ip_hash, window_start.timestamp())

            return attempts_count >= self.max_attempts
            
        except ValueError as e:
            logger.warning(f"Invalid IP address provided: {e}")
            return True

        except Exception as e:
            logger.error(f"Error checking IP block status: {e}")
            return False

    async def record_failed_attempt(self, ip_address: str, attempt_type: str = "auth") -> bool:
        """Record a failed authentication attempt for an IP address."""
        try:
            validated_ip = UniversalValidator.validate_ip_address(ip_address)
            ip_hash = self._get_ip_hash(validated_ip)

            current_time = datetime.now()
            attempt_data = {
                'ip_hash': ip_hash,
                'attempt_type': attempt_type,
                'attempted_at': int(current_time.timestamp()),
                'blocked_until': None,
                'created_at': current_time.isoformat()
            }

            return await db_service.record_ip_attempt(attempt_data)
            
        except ValueError as e:
            logger.warning(f"Invalid IP address for failed attempt: {e}")
            return False

        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")
            return False

    async def clear_ip_attempts(self, ip_address: str) -> bool:
        """Clear all attempts for an IP address (used after successful auth)."""

        try:
            validated_ip = UniversalValidator.validate_ip_address(ip_address)
            ip_hash = self._get_ip_hash(validated_ip)
            
            return await db_service.clear_ip_attempts(ip_hash)
            
        except ValueError as e:
            logger.warning(f"Invalid IP address for clearing attempts: {e}")
            return False

        except Exception as e:
            logger.error(f"Error clearing IP attempts: {e}")
            return False

    async def get_remaining_attempts(self, ip_address: str) -> int:
        """Get the number of remaining attempts for an IP address."""

        try:
            validated_ip = UniversalValidator.validate_ip_address(ip_address)
            ip_hash = self._get_ip_hash(validated_ip)
            
            current_time = datetime.now()
            window_start = current_time - timedelta(minutes=self.window_minutes)
            
            attempts_count = await db_service.get_ip_attempts_count(ip_hash, window_start.timestamp())
            
            return max(0, self.max_attempts - attempts_count)
            
        except ValueError as e:
            logger.warning(f"Invalid IP address for remaining attempts: {e}")
            return 0

        except Exception as e:
            logger.error(f"Error getting remaining attempts: {e}")
            return self.max_attempts

    async def cleanup_expired_attempts(self) -> int:
        """Clean up expired IP attempts (called periodically)."""

        try:
            cleanup_before = datetime.now() - timedelta(minutes=self.window_minutes * 2)
            return await db_service.cleanup_expired_ip_attempts(cleanup_before.timestamp())
            
        except Exception as e:
            logger.error(f"Error cleaning up expired IP attempts: {e}")
            return 0

ip_rate_limiter_service = IPRateLimiterService()
