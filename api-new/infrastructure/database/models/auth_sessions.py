"""
Auth Sessions Database Model.
Temporary storage for OAuth authentication flow with UUID polling.
"""

from sqlalchemy import Column, String, DateTime, func
from ..core import Base

class AuthSession(Base):
    """Temporary authentication session for OAuth polling flow"""
    
    __tablename__ = "auth_sessions"
    
    appid = Column(String(36), primary_key=True)  # UUID4 from app
    userid = Column(String(255), nullable=True)   # {provider}_{id} format, initially NULL
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<AuthSession(appid='{self.appid}', userid='{self.userid}')>"
