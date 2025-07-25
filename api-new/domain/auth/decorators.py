"""
Mode-based endpoint decorators for EchoTuner API.

This module contains decorators for controlling endpoint access based on 
demo mode, debug mode, and production mode settings.
"""

import logging

from fastapi import HTTPException
from functools import wraps

from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

def normal_only(func):
    """Decorator to restrict endpoints to normal mode only"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Always allow access since demo mode no longer exists
        return await func(*args, **kwargs)

    return wrapper


def demo_only(func):
    """Decorator to restrict endpoints to demo mode only - DEPRECATED"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Demo mode no longer exists - deny all access
        raise HTTPException(
            status_code=403, 
            detail="Demo mode endpoints are no longer available"
        )

    return wrapper


def debug_only(func):
    """Decorator to restrict endpoints to debug mode only"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            raise HTTPException(
                status_code=403, 
                detail="This endpoint is only available in debug mode"
            )

        return await func(*args, **kwargs)

    return wrapper
