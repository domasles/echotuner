"""
Mode-based endpoint decorators for EchoTuner API.

This module contains decorators for controlling endpoint access based on debug mode and production mode settings.
"""

import logging

from fastapi import HTTPException
from functools import wraps

from domain.config.settings import settings

logger = logging.getLogger(__name__)


def debug_only(func):
    """Decorator to restrict endpoints to debug mode only"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            raise HTTPException(status_code=403, detail="This endpoint is only available in debug mode")

        return await func(*args, **kwargs)

    return wrapper
