"""
Service-level decorators for standardizing service method patterns.
"""

import logging

from typing import Callable, Any
from functools import wraps

def service_operation(operation_name: str = None, return_on_error: Any = None, log_errors: bool = True):
    """
    Decorator for service operations with standardized error handling.
    
    Args:
        operation_name: Optional name for the operation (uses function name if not provided)
        return_on_error: Value to return on error (default: None)
        log_errors: Whether to log errors (default: True)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"{name} failed: {e}")
                return return_on_error
        return wrapper
    return decorator

def service_optional_operation(operation_name: str = None):
    """
    Decorator for service operations that return optional values.
    Returns None on error.
    """

    return service_operation(operation_name, return_on_error=None)

def service_bool_operation(operation_name: str = None):
    """
    Decorator for service operations that return boolean.
    Returns False on error.
    """

    return service_operation(operation_name, return_on_error=False)

def service_list_operation(operation_name: str = None):
    """
    Decorator for service operations that return lists.
    Returns empty list on error.
    """

    return service_operation(operation_name, return_on_error=[])
