"""
Rate limiting ORM models.
Unified rate limiting system for all users.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from datetime import datetime

from ..core import Base


class RateLimit(Base):
    """Rate limits table for request tracking."""

    __tablename__ = "rate_limits"

    user_id = Column(String(255), ForeignKey("user_accounts.user_id"), primary_key=True)
    requests_count = Column(Integer, default=0)
    last_request_date = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def __repr__(self):
        return f"<RateLimit(user_id='{self.user_id}', count={self.requests_count})>"
