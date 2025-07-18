"""
Modern database layer for EchoTuner API.
Provides ORM-based database operations with SQLAlchemy.
"""

from .core import DatabaseCore, get_session
from .models import *

__all__ = [
    'UserPersonality',
    'SpotifyPlaylist',
    'DeviceRegistry',
    'EmbeddingCache',
    'PlaylistDraft', 
    'DatabaseCore',
    'DemoPlaylist',
    'AuthSession',
    'AuthAttempt',
    'AuthState',
    'RateLimit',
    'IPAttempt',

    'get_session',
]
