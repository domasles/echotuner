"""
Session management decorators for AI providers.

This module contains decorators for managing aiohttp sessions across AI providers.
"""

from functools import wraps
from typing import Callable, Any


def ensure_session_initialized(func: Callable) -> Callable:
    """
    Decorator to ensure aiohttp session is initialized before method execution.
    
    This decorator checks if the provider's session is initialized and calls
    the initialize method if needed before executing the wrapped method.
    
    Args:
        func: The method to wrap
        
    Returns:
        Wrapped method with session initialization check
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> Any:
        if self._session is None:
            await self.initialize()
        return await func(self, *args, **kwargs)
    return wrapper
