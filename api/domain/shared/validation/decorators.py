"""
Validation decorators for standardizing validation method patterns.
"""

import logging

from functools import wraps
from typing import Callable
from datetime import datetime

from fastapi import HTTPException, Request

from infrastructure.database.repository import repository
from infrastructure.database.models import UserAccount
from domain.config.settings import settings

logger = logging.getLogger(__name__)


def validate_request_headers():
    """
    Decorator for session-token-based authentication.
    Reads X-Auth-Token, looks up the corresponding user in the DB, and injects validated_user_id.
    Note: The endpoint function MUST have 'request: Request' as first parameter.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            session_token = request.headers.get("X-Auth-Token") or request.headers.get("x-auth-token")

            if not session_token:
                logger.error("VALIDATOR: Missing X-Auth-Token header")
                raise HTTPException(status_code=401, detail="Missing X-Auth-Token header")

            user_account = await repository.get_by_field(UserAccount, "session_token", session_token)

            if not user_account:
                logger.error("VALIDATOR: Invalid or expired session token")
                raise HTTPException(status_code=401, detail="Invalid or expired session token")

            # Check session token expiry if configured
            if settings.SESSION_TOKEN_EXPIRY_DAYS > 0 and user_account.session_token_expires_at is not None:
                if datetime.now() > user_account.session_token_expires_at:
                    logger.warning(f"VALIDATOR: Session token expired for user {user_account.user_id}")
                    await repository.update_by_conditions(
                        UserAccount,
                        {"session_token": session_token},
                        {"session_token": None, "session_token_expires_at": None},
                    )
                    raise HTTPException(status_code=401, detail="Session token expired")

            # Add validated user_id to kwargs for the endpoint function
            kwargs["validated_user_id"] = user_account.user_id

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
