"""Clean database module with proper separation of concerns."""

# Core database functionality
from .core import get_session

# Generic repository pattern  
from .repository import repository

# Models (for domain services to import)
from .models import *

__all__ = ['get_session', 'repository']
