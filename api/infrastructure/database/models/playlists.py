"""
Playlist related ORM models.
Unified playlist system for all users (Spotify and Google).
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, Index

from ..core import Base


class PlaylistDraft(Base):
    """Playlist drafts table for all users."""

    __tablename__ = "playlist_drafts"

    id = Column(String, primary_key=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id"), nullable=False)
    prompt = Column(Text, nullable=False)
    songs_json = Column(Text, nullable=False)
    status = Column(String, default="draft")
    spotify_playlist_id = Column(String)
    spotify_playlist_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_playlist_drafts_user_id", "user_id"),
        Index("idx_playlist_drafts_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<PlaylistDraft(id='{self.id}', user_id='{self.user_id}')>"


class SpotifyPlaylist(Base):
    """Spotify playlists table for tracking created playlists."""

    __tablename__ = "spotify_playlists"

    spotify_playlist_id = Column(String, primary_key=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id"), nullable=False)
    original_draft_id = Column(String, ForeignKey("playlist_drafts.id"))
    playlist_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (Index("idx_spotify_playlists_user_id", "user_id"),)

    def __repr__(self):
        return f"<SpotifyPlaylist(id='{self.spotify_playlist_id}', user_id='{self.user_id}')>"
