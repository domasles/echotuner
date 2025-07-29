# A file used to make endpoints a Python package

# Import routers - this is what main.py actually needs
from .auth import router as auth_router  
from .playlist import router as playlist_router
from .personality import router as personality_router
from .ai import router as ai_router
from .config import router as config_router
from .server import router as server_router

# Import the root function from config controller
from .config import root

__all__ = [
    'auth_router',
    'playlist_router', 
    'spotify_router',
    'personality_router',
    'ai_router', 
    'config_router',
    'server_router',
    'root'
]
