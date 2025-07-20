"""
Rate limiter service.
Enforces rate limits on user requests.
"""

import hashlib
import logging

from datetime import datetime, timedelta

from application.core.singleton import SingletonServiceBase
from application import RateLimitStatus

from infrastructure.config.settings import settings

from infrastructure.database.service import db_service

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class RateLimiterService(SingletonServiceBase):
    """
    Service to handle rate limiting for playlist generation requests.
    Tracks requests per device and enforces daily limits.
    """

    def _setup_service(self):
        """Initialize the RateLimiterService."""

        self.is_rate_limiting_enabled = settings.PLAYLIST_LIMIT_ENABLED
        self.max_requests_per_day = settings.MAX_PLAYLISTS_PER_DAY

        self._log_initialization("Rate limiter service initialized successfully", logger)

    def __init__(self):
        super().__init__()

    async def initialize(self):
        """Initialize the database and create tables if needed"""

        try:
            pass  # Rate limiter ready

        except Exception as e:
            logger.error(f"Error initializing rate limiter: {e}")
            sanitized_error = UniversalValidator.sanitize_error_message(str(e))

            raise RuntimeError(f"Rate limiter initialization failed: {sanitized_error}")

    def _get_device_hash(self, device_id: str) -> str:
        """Create a hash of the device ID for privacy"""

        return hashlib.sha256(device_id.encode()).hexdigest()

    def _is_same_day(self, timestamp: str) -> bool:
        """Check if a timestamp is from the same day as today"""

        try:
            request_date = datetime.fromisoformat(timestamp).date()
            today = datetime.now().date()

            return request_date == today

        except:
            return False

    async def can_make_request(self, device_id: str) -> bool:
        """Check if a device can make a new playlist request"""

        if not self.is_rate_limiting_enabled:
            return True

        try:
            device_hash = self._get_device_hash(device_id)
            current_date = datetime.now().date().isoformat()

            rate_data = await db_service.get_rate_limit_status(device_hash, current_date)

            if not rate_data:
                return True

            requests_count = rate_data.get('requests_count', 0)
            last_request_date = rate_data.get('last_request_date', '')

            if not self._is_same_day(last_request_date):
                return True

            return requests_count < self.max_requests_per_day

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True

    async def record_request(self, device_id: str):
        """Record a playlist generation request"""

        try:
            device_hash = self._get_device_hash(device_id)
            current_date = datetime.now().date().isoformat()

            rate_data = await db_service.get_rate_limit_status(device_hash, current_date)

            if rate_data:
                request_count = rate_data.get('requests_count', 0)
                last_request_date = rate_data.get('last_request_date', '')

                if not self._is_same_day(last_request_date):
                    request_count = 0

                new_count = request_count + 1
                await db_service.update_rate_limit_requests(device_hash, current_date, new_count)

            else:
                await db_service.update_rate_limit_requests(device_hash, current_date, 1)

        except Exception as e:
            logger.error(f"Error recording request: {e}")

    async def get_status(self, device_id: str) -> RateLimitStatus:
        """Get current rate limit status for a device"""

        device_hash = self._get_device_hash(device_id)

        try:
            current_date = datetime.now().date().isoformat()
            rate_data = await db_service.get_rate_limit_status(device_hash, current_date)

            if not rate_data:
                return RateLimitStatus(
                    device_id=device_id,
                    requests_made_today=0,
                    max_requests_per_day=self.max_requests_per_day,
                    can_make_request=True,
                    playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
                )

            request_count = rate_data.get('requests_count', 0)
            last_request_date = rate_data.get('last_request_date', '')

            if not self._is_same_day(last_request_date):
                request_count = 0

            tomorrow = datetime.now().date() + timedelta(days=1)
            reset_time = datetime.combine(tomorrow, datetime.min.time()).isoformat()

            return RateLimitStatus(
                device_id=device_id,
                requests_made_today=request_count,
                max_requests_per_day=self.max_requests_per_day,
                can_make_request=request_count < self.max_requests_per_day if self.is_rate_limiting_enabled else True,
                reset_time=reset_time,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
            )

        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")

            return RateLimitStatus(
                device_id=device_id,
                requests_made_today=0,
                max_requests_per_day=self.max_requests_per_day,
                can_make_request=True,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
            )

    async def reset_daily_limits(self):
        """Reset all daily limits (for testing purposes)"""

        try:
            await db_service.delete_record('rate_limits', '1=1')
            logger.info("Daily limits reset successfully")

        except Exception as e:
            logger.error(f"Error resetting daily limits: {e}")

rate_limiter_service = RateLimiterService()
