"""
Authentication related ORM models.
Unified authentication system supporting Spotify and Google OAuth.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, func
from ..core import Base

class UserAccount(Base):
    """Unified user account table for both Spotify and Google users."""

    __tablename__ = "user_accounts"

    user_id = Column(String(255), primary_key=True)  # Format: spotify_{id} or google_{id}
    provider = Column(String(50), nullable=False)    # 'spotify' or 'google'
    provider_user_id = Column(String(255), nullable=False)  # Original ID from provider
    display_name = Column(String(255), nullable=True)  # Display name from provider
    email = Column(String(255), nullable=True)        # Email from provider
    profile_picture_url = Column(Text, nullable=True)  # Profile picture URL from provider
    access_token = Column(Text, nullable=True)       # User's own tokens (Normal mode only)
    refresh_token = Column(Text, nullable=True)      # User's own tokens (Normal mode only)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserAccount(user_id='{self.user_id}', provider='{self.provider}')>"

class AuthAttempt(Base):
    """Rate limiting for authentication attempts per IP."""

    __tablename__ = "auth_attempts"

    ip_address = Column(String(45), primary_key=True)  # Support IPv6
    attempt_count = Column(Integer, default=0)
    window_start = Column(Integer, nullable=False)
    last_attempt = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<AuthAttempt(ip='{self.ip_address}', count={self.attempt_count})>"

class AuthState(Base):
    """OAuth state storage for CSRF protection."""

    __tablename__ = "auth_states"

    state = Column(String(255), primary_key=True)  # OAuth state parameter
    appid = Column(String(36), nullable=True)      # App ID for linking to auth session
    platform = Column(String(50), nullable=False)  # 'spotify' or 'google'
    created_at = Column(Integer, nullable=False)    # Unix timestamp
    expires_at = Column(Integer, nullable=False)    # Unix timestamp

    def __repr__(self):
        return f"<AuthState(state='{self.state[:8]}...', platform='{self.platform}')>"
