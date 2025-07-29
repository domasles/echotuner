"""
User related ORM models.
Unified user personality system for all users.
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, func

from ..core import Base

class UserPersonality(Base):
    """User personality data table for all users (Spotify and Google)."""

    __tablename__ = "user_personalities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id"), nullable=False, unique=True)
    user_context = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserPersonality(user_id='{self.user_id}')>"
