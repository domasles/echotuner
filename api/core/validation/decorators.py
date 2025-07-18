"""
Validation decorators for standardizing validation method patterns.
"""

from functools import wraps
from typing import Callable

from core.validation.validators import UniversalValidator, validate_request, validate_input

def validate_request_data(validation_func: Callable = None, **validation_kwargs):
    """
    Decorator for validating request inputs.
    
    Args:
        validation_func: Function to use for validation
        **validation_kwargs: Additional validation parameters
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Apply validation logic here
            if validation_func:
                # Apply custom validation
                pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input_data(input_type: str = "general"):
    """
    Decorator for input validation.
    
    Args:
        input_type: Type of input to validate (prompt, session_id, etc.)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Apply input validation based on type
            return await func(*args, **kwargs)
        return wrapper
    return decorator


