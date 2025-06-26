import hashlib
import logging
import sqlite3

from datetime import datetime, timedelta
from core.models import RateLimitStatus
from config.settings import settings

logger = logging.getLogger(__name__)

class RateLimiterService:
    """
    Service to handle rate limiting for playlist generation requests.
    Tracks requests per device and enforces daily limits.
    """
    
    def __init__(self):
        self.db_path = settings.DATABASE_FILENAME
        self.max_refinements = settings.MAX_REFINEMENTS_PER_PLAYLIST

        self.is_rate_limiting_enabled = settings.PLAYLIST_LIMIT_ENABLED
        self.max_requests_per_day = settings.MAX_PLAYLISTS_PER_DAY

        self.initialized = False
    
    async def initialize(self):
        """Initialize the database and create tables if needed"""

        try:
            self._create_tables()
            logger.info("Rate limiter initialized successfully")
            self.initialized = True

        except RuntimeError:
            raise

        except Exception as e:
            logger.error(f"Error initializing rate limiter: {e}")
            raise RuntimeError(f"Rate limiter initialization failed: {e}")

    def is_ready(self) -> bool:
        """Check if the service is ready"""
        
        return self.initialized
    
    def _create_tables(self):
        """Create database tables for rate limiting"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_requests (
                device_id TEXT PRIMARY KEY,
                request_count INTEGER DEFAULT 0,
                last_request_date TEXT,
                refinement_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
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
        
        if not self.initialized:
            await self.initialize()
        
        try:
            device_hash = self._get_device_hash(device_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT request_count, last_request_date FROM daily_requests WHERE device_id = ?",
                (device_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return True
            
            request_count, last_request_date = result

            if not self._is_same_day(last_request_date):
                return True
            
            return request_count < self.max_requests_per_day
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True
    
    async def can_refine_playlist(self, device_id: str) -> bool:
        """Check if a device can refine a playlist (max 3 refinements)"""

        if not settings.REFINEMENT_LIMIT_ENABLED:
            return True

        if not self.initialized:
            await self.initialize()
        
        try:
            device_hash = self._get_device_hash(device_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT refinement_count, last_request_date FROM daily_requests WHERE device_id = ?",
                (device_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return True
            
            refinement_count, last_request_date = result

            if not self._is_same_day(last_request_date):
                return True
            
            return refinement_count < self.max_refinements
        
        except Exception as e:
            logger.error(f"Error checking refinement limit: {e}")
            return True
    
    async def record_request(self, device_id: str):
        """Record a playlist generation request"""

        if not self.initialized:
            await self.initialize()
        
        try:
            device_hash = self._get_device_hash(device_id)
            current_time = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT request_count, last_request_date FROM daily_requests WHERE device_id = ?",
                (device_hash,)
            )
            
            result = cursor.fetchone()
            
            if result:
                request_count, last_request_date = result

                if not self._is_same_day(last_request_date):
                    request_count = 0

                new_count = request_count + 1
                
                cursor.execute(
                    "UPDATE daily_requests SET request_count = ?, last_request_date = ? WHERE device_id = ?",
                    (new_count, current_time, device_hash)
                )
            else:
                cursor.execute(
                    "INSERT INTO daily_requests (device_id, request_count, last_request_date, refinement_count) VALUES (?, 1, ?, 0)",
                    (device_hash, current_time)
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    async def record_refinement(self, device_id: str):
        """Record a playlist refinement request"""

        if not self.initialized:
            await self.initialize()
        
        try:
            device_hash = self._get_device_hash(device_id)
            current_time = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT refinement_count, last_request_date FROM daily_requests WHERE device_id = ?",
                (device_hash,)
            )
            
            result = cursor.fetchone()
            
            if result:
                refinement_count, last_request_date = result

                if not self._is_same_day(last_request_date):
                    refinement_count = 0

                new_count = refinement_count + 1
                
                cursor.execute(
                    "UPDATE daily_requests SET refinement_count = ?, last_request_date = ? WHERE device_id = ?",
                    (new_count, current_time, device_hash)
                )
            else:
                cursor.execute(
                    "INSERT INTO daily_requests (device_id, request_count, last_request_date, refinement_count) VALUES (?, 0, ?, 1)",
                    (device_hash, current_time)
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording refinement: {e}")
    
    async def get_status(self, device_id: str) -> RateLimitStatus:
        """Get current rate limit status for a device"""

        device_hash = self._get_device_hash(device_id)
        
        if not self.initialized:
            await self.initialize()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT request_count, refinement_count, last_request_date FROM daily_requests WHERE device_id = ?",
                (device_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return RateLimitStatus(
                    device_id=device_id,
                    requests_made_today=0,
                    max_requests_per_day=self.max_requests_per_day,
                    refinements_used=0,
                    max_refinements=self.max_refinements,
                    can_make_request=True,
                    can_refine=True,
                    playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED,
                    refinement_limit_enabled=settings.REFINEMENT_LIMIT_ENABLED
                )
            
            request_count, refinement_count, last_request_date = result

            if not self._is_same_day(last_request_date):
                request_count = 0
                refinement_count = 0

            tomorrow = datetime.now().date() + timedelta(days=1)
            reset_time = datetime.combine(tomorrow, datetime.min.time()).isoformat()
            
            return RateLimitStatus(
                device_id=device_id,
                requests_made_today=request_count,
                max_requests_per_day=self.max_requests_per_day,
                refinements_used=refinement_count,
                max_refinements=self.max_refinements,
                can_make_request=request_count < self.max_requests_per_day if self.is_rate_limiting_enabled else True,
                can_refine=refinement_count < self.max_refinements,
                reset_time=reset_time,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED,
                refinement_limit_enabled=settings.REFINEMENT_LIMIT_ENABLED
            )
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")

            return RateLimitStatus(
                device_id=device_id,
                requests_made_today=0,
                max_requests_per_day=self.max_requests_per_day,
                refinements_used=0,
                max_refinements=self.max_refinements,
                can_make_request=True,
                can_refine=True,
                playlist_limit_enabled=settings.PLAYLIST_LIMIT_ENABLED,
                refinement_limit_enabled=settings.REFINEMENT_LIMIT_ENABLED
            )
    
    async def reset_daily_limits(self):
        """Reset all daily limits (for testing purposes)"""

        if not self.initialized:
            await self.initialize()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM daily_requests")
            
            conn.commit()
            conn.close()
            
            logger.info("Daily limits reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting daily limits: {e}")
