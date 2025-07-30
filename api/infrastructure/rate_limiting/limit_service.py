"""
Rate limiter service.
Enforces rate limits on user requests.
"""

import hashlib
import logging

from datetime import datetime, timedelta

from infrastructure.singleton import SingletonServiceBase
from application import RateLimitStatus

from domain.config.settings import settings

from infrastructure.database.repository import repository
from infrastructure.database.models.rate_limits import RateLimit

from domain.shared.validation.validators import UniversalValidator

logger = logging.getLogger(__name__)

class RateLimiterService(SingletonServiceBase):
    """
    Service to handle rate limiting for playlist generation requests.
    Tracks requests per device and enforces daily limits.
    """

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the RateLimiterService."""

        self.is_rate_limiting_enabled = settings.PLAYLIST_LIMIT_ENABLED
        self.max_requests_per_day = settings.MAX_PLAYLISTS_PER_DAY
        self.repository = repository

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

            rate_limit = await self.repository.get_by_field(RateLimit, 'user_id', device_hash)

            if not rate_limit:
                return True

            requests_count = rate_limit.requests_count
            last_request_date = rate_limit.last_request_date

            if not self._is_same_day(last_request_date):
                return True

            return requests_count < self.max_requests_per_day

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True

    async def record_request(self, user_id: str):
        """Record a playlist generation request"""

        try:
            user_hash = self._get_device_hash(user_id)  # Reuse hash function for consistency
            current_date = datetime.now().date()

            rate_limit = await self.repository.get_by_field(RateLimit, 'user_id', user_hash)

            if rate_limit:
                request_count = rate_limit.requests_count
                last_request_date = rate_limit.last_request_date

                if not self._is_same_day(last_request_date):
                    request_count = 0

                new_count = request_count + 1
                await self.repository.update(RateLimit, user_hash, {
                    'requests_count': new_count,
                    'last_request_date': current_date,
                    'updated_at': datetime.now()
                }, id_field='user_id')

            else:
                await self.repository.create(RateLimit, {
                    'user_id': user_hash,
                    'requests_count': 1,
                    'last_request_date': current_date,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })

        except Exception as e:
            logger.error(f"Error recording request: {e}")

    async def get_status(self, user_id: str) -> RateLimitStatus:
        """Get current rate limit status for a user"""

        user_hash = self._get_device_hash(user_id)  # Reuse hash function for consistency

        try:
            current_date = datetime.now().date().isoformat()
            rate_limit = await self.repository.get_by_field(RateLimit, 'user_id', user_hash)

            if not rate_limit:
                return RateLimitStatus(
                    user_id=user_id,
                    requests_made_today=0,
                    max_requests_per_day=self.max_requests_per_day,
                    can_make_request=True,
                    playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
                )

            request_count = rate_limit.requests_count
            last_request_date = rate_limit.last_request_date

            if not self._is_same_day(last_request_date):
                request_count = 0

            tomorrow = datetime.now().date() + timedelta(days=1)
            reset_time = datetime.combine(tomorrow, datetime.min.time()).isoformat()

            return RateLimitStatus(
                user_id=user_id,
                requests_made_today=request_count,
                max_requests_per_day=self.max_requests_per_day,
                can_make_request=request_count < self.max_requests_per_day if self.is_rate_limiting_enabled else True,
                reset_time=reset_time,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
            )

        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")

            return RateLimitStatus(
                user_id=user_id,
                requests_made_today=0,
                max_requests_per_day=self.max_requests_per_day,
                can_make_request=True,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED
            )

    async def reset_daily_limits(self):
        """Reset all daily limits (for testing purposes)"""

        try:
            # Delete all rate limit records
            rate_limits = await self.repository.list_with_conditions(RateLimit, [])
            for rate_limit in rate_limits:
                await self.repository.delete(RateLimit, rate_limit.user_id, id_field='user_id')
            logger.info("Daily limits reset successfully")

        except Exception as e:
            logger.error(f"Error resetting daily limits: {e}")

rate_limiter_service = RateLimiterService()
