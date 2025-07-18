"""
Authentication related ORM models.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..core import Base

class DeviceRegistry(Base):
    """Device registry table for managing registered devices."""

    __tablename__ = "device_registry"

    device_id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    app_version = Column(String)
    device_fingerprint = Column(String)
    registration_timestamp = Column(Integer, nullable=False)
    last_seen_timestamp = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    sessions = relationship("AuthSession", back_populates="device", cascade="all, delete-orphan")
    auth_states = relationship("AuthState", back_populates="device", cascade="all, delete-orphan")

class AuthSession(Base):
    """Authentication session table."""

    __tablename__ = "auth_sessions"

    session_id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("device_registry.device_id"), nullable=False)
    platform = Column(String, nullable=False)
    spotify_user_id = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(Integer)
    created_at = Column(Integer, nullable=False)
    last_used_at = Column(Integer, nullable=False)
    account_type = Column(String, default='normal')

    device = relationship("DeviceRegistry", back_populates="sessions")

class AuthState(Base):
    """Authentication state table for OAuth flow."""

    __tablename__ = "auth_states"

    state = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("device_registry.device_id"), nullable=False)
    platform = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)
    expires_at = Column(Integer, nullable=False)

    device = relationship("DeviceRegistry", back_populates="auth_states")

class AuthAttempt(Base):
    """Authentication attempts table for rate limiting."""

    __tablename__ = "auth_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    platform = Column(String, nullable=False) 
    attempted_at = Column(Integer, nullable=False)
    expires_at = Column(Integer, nullable=False)
    success = Column(Boolean, default=False)

class DemoOwnerToken(Base):
    """Demo owner token storage for demo mode bypass."""

    __tablename__ = "demo_owner_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(Integer, nullable=False)
    spotify_user_id = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)
