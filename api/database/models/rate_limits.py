"""
Rate limiting ORM models.
"""

from sqlalchemy import Column, String, Integer, Float

from ..core import Base

class RateLimit(Base):
    """Rate limits table for request/refinement tracking."""
    
    __tablename__ = "rate_limits"
    
    user_id = Column(String, primary_key=True)
    requests_count = Column(Integer, default=0)
    refinements_count = Column(Integer, default=0)
    last_request_date = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

class IPAttempt(Base):
    """IP attempt tracking table for IP-based rate limiting."""
    
    __tablename__ = "ip_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_hash = Column(String, nullable=False)
    attempt_type = Column(String, nullable=False, default='auth')
    attempted_at = Column(Integer, nullable=False)
    blocked_until = Column(Integer)
    created_at = Column(String, nullable=False)
