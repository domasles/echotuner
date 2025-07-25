"""
Rate limiting ORM models.
Unified rate limiting system for all users.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func

from ..core import Base

class RateLimit(Base):
    """Rate limits table for request tracking."""
    
    __tablename__ = "rate_limits"
    
    user_id = Column(String(255), ForeignKey("user_accounts.user_id"), primary_key=True)
    requests_count = Column(Integer, default=0)
    last_request_date = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RateLimit(user_id='{self.user_id}', count={self.requests_count})>"

class IPAttempt(Base):
    """IP attempt tracking table for IP-based rate limiting."""
    
    __tablename__ = "ip_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_hash = Column(String, nullable=False)
    attempt_type = Column(String, nullable=False, default='auth')
    attempted_at = Column(Integer, nullable=False)
    blocked_until = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<IPAttempt(ip_hash='{self.ip_hash}', type='{self.attempt_type}')>"
