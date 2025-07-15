"""
Database operation decorators for EchoTuner API.

This module contains decorators for database operations with automatic
session management, error handling, and transaction control.
"""

import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


def db_write_operation(operation_name: str, log_success: bool = True, raise_on_error: bool = True, return_on_error=None):
    """
    Decorator for database write operations.
    Provides:
    - Session management
    - Error handling and logging
    - Transaction management
    - Consistent return patterns
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                from database.core import get_session
                async with get_session() as session:
                    result = await func(session, *args, **kwargs)
                    await session.commit()
                    
                    if log_success:
                        logger.debug(f"{operation_name} completed successfully")
                    
                    return result
                    
            except Exception as e:
                error_msg = f"{operation_name} failed: {e}"
                logger.error(error_msg)
                
                if raise_on_error:
                    # Import UniversalValidator here to avoid circular imports
                    try:
                        from utils.input_validator import UniversalValidator
                        from utils.exceptions import OperationFailedError
                        raise OperationFailedError(UniversalValidator.sanitize_error_message(str(e)))
                    except ImportError:
                        from utils.exceptions import OperationFailedError
                        raise OperationFailedError(str(e))
                
                return return_on_error
                
        return wrapper
    return decorator


def db_read_operation(operation_name: str):
    """
    Decorator for read-only database operations.
    No transaction commit needed.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                from database.core import get_session
                async with get_session() as session:
                    result = await func(session, *args, **kwargs)
                    logger.debug(f"{operation_name} completed successfully")
                    return result
                    
            except Exception as e:
                logger.error(f"{operation_name} failed: {e}")
                return None
                
        return wrapper
    return decorator
