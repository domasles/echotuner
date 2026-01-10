"""
Auth Sessions Database Model.
Temporary storage for OAuth authentication flow with UUID polling.
"""

from sqlalchemy import Column, String, DateTime, func
from ..core import Base


class AuthSession(Base):
    """Temporary authentication session for OAuth polling flow"""

    __tablename__ = "auth_sessions"

    app_id = Column(String(36), primary_key=True)  # UUID4 from app
    user_id = Column(String(255), nullable=True)  # {provider}_{id} format, initially NULL
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<AuthSession(app_id='{self.app_id}', user_id='{self.user_id}')>"
