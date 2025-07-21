"""Clean database module with proper separation of concerns."""

# Core database functionality
from .core import db_service, get_session

# Generic repository pattern  
from .repository import repository

# Models (for domain services to import)
from .models import *

__all__ = ['db_service', 'get_session', 'repository']
