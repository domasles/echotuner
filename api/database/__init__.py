"""
Modern database layer for EchoTuner API.
Provides ORM-based database operations with SQLAlchemy.
"""

from .core import DatabaseCore, get_session
from .models import *

__all__ = [
    'DatabaseCore',
    'get_session',
    'AuthSession',
    'DeviceRegistry', 
    'AuthState',
    'AuthAttempt',
    'PlaylistDraft',
    'SpotifyPlaylist',
    'DemoPlaylist',
    'UserPersonality',
    'RateLimit',
    'IPAttempt',
    'EmbeddingCache'
]
