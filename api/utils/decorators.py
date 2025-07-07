import logging

from fastapi import HTTPException
from functools import wraps

from config.settings import settings

logger = logging.getLogger(__name__)

def demo_mode_restricted(func):
    """Decorator to restrict endpoints when in demo mode"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if settings.DEMO:
            raise HTTPException(
                status_code=403, 
                detail="This endpoint is not available in demo mode"
            )

        return await func(*args, **kwargs)

    return wrapper

def normal_mode_restricted(func):
    """Decorator to restrict endpoints when in normal mode"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not settings.DEMO:
            raise HTTPException(
                status_code=403, 
                detail="This endpoint is not available in normal mode"
            )

        return await func(*args, **kwargs)

    return wrapper

def debug_only(func):
    """Decorator to restrict endpoints to debug mode only"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            logger.warning(f"Debug-only endpoint '{func.__name__}' accessed in production mode")

            raise HTTPException(
                status_code=403, 
                detail="This endpoint is only available in debug mode"
            )

        return await func(*args, **kwargs)

    return wrapper

def production_safe(func):
    """Decorator to mark endpoints as production-safe"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper
