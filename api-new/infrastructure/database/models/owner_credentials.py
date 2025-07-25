"""
Owner Spotify Credentials Database Model.
Stores owner's Spotify tokens for shared mode operations.
"""

from sqlalchemy import Column, String, DateTime, func
from ..core import Base

class OwnerSpotifyCredentials(Base):
    """Owner's Spotify credentials for shared mode"""
    
    __tablename__ = "owner_spotify_credentials"
    
    id = Column(String(36), primary_key=True, default="owner")  # Single record
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    spotify_user_id = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<OwnerSpotifyCredentials(spotify_user_id='{self.spotify_user_id}')>"
