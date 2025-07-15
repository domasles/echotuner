"""
Playlist related ORM models.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..core import Base

class PlaylistDraft(Base):
    """Playlist drafts table."""
    
    __tablename__ = "playlist_drafts"
    
    id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("device_registry.device_id"), nullable=False)
    session_id = Column(String, ForeignKey("auth_sessions.session_id"))
    prompt = Column(Text, nullable=False)
    songs_json = Column(Text, nullable=False)
    songs = Column(Text)
    is_draft = Column(Boolean, default=True)
    status = Column(String, default='draft')
    spotify_playlist_id = Column(String)
    spotify_playlist_url = Column(String)
    created_at = Column(String, nullable=False)  # Using string for timestamp compatibility
    updated_at = Column(String, nullable=False)

class SpotifyPlaylist(Base):
    """Spotify playlists table for tracking created playlists."""
    
    __tablename__ = "echotuner_spotify_playlists"
    
    spotify_playlist_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    device_id = Column(String, ForeignKey("device_registry.device_id"), nullable=False)
    session_id = Column(String, ForeignKey("auth_sessions.session_id"))
    original_draft_id = Column(String, ForeignKey("playlist_drafts.id"))
    playlist_name = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

class DemoPlaylist(Base):
    """Demo playlists table for tracking demo account playlists."""
    
    __tablename__ = "demo_playlists"
    
    playlist_id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("device_registry.device_id"), nullable=False)
    session_id = Column(String, ForeignKey("auth_sessions.session_id"))
    prompt = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
