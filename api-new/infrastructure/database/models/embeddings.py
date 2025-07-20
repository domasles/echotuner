"""
Embedding cache ORM model.
"""

from sqlalchemy import Column, String, Text, Integer, JSON

from ..service import Base

class EmbeddingCache(Base):
    """Embedding cache table for storing AI response vectors."""

    __tablename__ = "embedding_cache"

    cache_key = Column(String, primary_key=True)  # SHA256 hash of prompt + context
    prompt = Column(Text, nullable=False)
    user_context = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False)
    last_accessed = Column(String, nullable=True)
    access_count = Column(Integer, default=1)
