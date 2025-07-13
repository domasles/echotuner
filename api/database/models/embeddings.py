"""
Embedding cache ORM model.
"""

from sqlalchemy import Column, String, Text, Integer, JSON

from ..core import Base

class EmbeddingCache(Base):
    """Embedding cache table for storing AI response vectors."""
    
    __tablename__ = "embedding_cache"
    
    cache_key = Column(String, primary_key=True)  # SHA256 hash of prompt + context
    prompt = Column(Text, nullable=False)  # Original prompt
    user_context = Column(Text, nullable=True)  # User context
    response_data = Column(JSON, nullable=False)  # AI response data
    created_at = Column(String, nullable=False)
    last_accessed = Column(String, nullable=True)
    access_count = Column(Integer, default=1)
