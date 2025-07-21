"""
User related ORM models.
"""

from sqlalchemy import Column, String, Integer, Text

from ..core import Base

class UserPersonality(Base):
    """User personality data table."""

    __tablename__ = "user_personalities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, unique=True)
    spotify_user_id = Column(String)

    user_context = Column(Text, nullable=False)  # JSON string
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
