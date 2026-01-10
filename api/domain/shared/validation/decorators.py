"""
Validation decorators for standardizing validation method patterns.
"""

import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def validate_request_headers():
    """
    Decorator for automatic user_id validation from headers.
    Validates user_id from request headers.
    Note: The endpoint function MUST have 'request: Request' as first parameter.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get user_id from headers (check both cases)
            user_id = request.headers.get("X-User-ID") or request.headers.get("x-user-id")
            logger.debug(f"Extracted user_id: '{user_id}'")

            if not user_id:
                logger.error("VALIDATOR: Missing X-User-ID header")
                raise HTTPException(status_code=422, detail="Missing X-User-ID header")

            # Validate user_id format (should be spotify_{id} or google_{id})
            if not (user_id.startswith("spotify_") or user_id.startswith("google_")):
                logger.error(f"VALIDATOR: Invalid X-User-ID format: '{user_id}'")
                raise HTTPException(status_code=422, detail="Invalid X-User-ID format")

            # Add validated user_id to kwargs for the endpoint function
            kwargs["validated_user_id"] = user_id

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
