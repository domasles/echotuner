"""Clean database module with proper separation of concerns."""

# Generic repository pattern  
from .repository import repository

# Models (for domain services to import)
from .models import *

__all__ = ['repository']
