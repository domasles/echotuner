"""
Authentication related ORM models.
Unified authentication system supporting Spotify and Google OAuth.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from datetime import datetime

from ..core import Base


class UserAccount(Base):
    """Unified user account table for both Spotify and Google users."""

    __tablename__ = "user_accounts"

    user_id = Column(String(255), primary_key=True)  # Format: spotify_{id} or google_{id}
    provider = Column(String(50), nullable=False)  # 'spotify' or 'google'
    provider_user_id = Column(String(255), nullable=False)  # Original ID from provider
    display_name = Column(String(255), nullable=True)  # Real name from provider
    access_token = Column(Text, nullable=True)  # User's own tokens (Normal mode only)
    refresh_token = Column(Text, nullable=True)  # User's own tokens (Normal mode only)
    expires_at = Column(DateTime, nullable=True)
    session_token = Column(String(64), unique=True, nullable=True, index=True)  # Opaque auth token sent by client
    created_at = Column(DateTime, default=datetime.now())
    last_used_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def __repr__(self):
        return f"<UserAccount(user_id='{self.user_id}', provider='{self.provider}')>"


class AuthState(Base):
    """OAuth state storage for CSRF protection."""

    __tablename__ = "auth_states"

    state = Column(String(255), primary_key=True)  # OAuth state parameter
    app_id = Column(String(36), nullable=True)  # App ID for linking to auth session
    platform = Column(String(50), nullable=False)  # 'spotify' or 'google'
    created_at = Column(Integer, nullable=False)  # Unix timestamp
    expires_at = Column(Integer, nullable=False)  # Unix timestamp

    def __repr__(self):
        return f"<AuthState(state='{self.state[:8]}...', platform='{self.platform}')>"
