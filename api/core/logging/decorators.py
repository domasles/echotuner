"""
Logging and error handling decorators for EchoTuner API.

This module provides decorators for standardizing logging and error handling
across the application, reducing code duplication and improving consistency.
"""

import logging
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import HTTPException

from core.validation.validators import UniversalValidator


def log_endpoint_call(operation_name: str, log_level: str = "info"):
    """
    Decorator to log endpoint calls with consistent formatting.
    
    Args:
        operation_name: Name of the operation being performed
        log_level: Logging level (info, debug, warning, error)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            
            # Log the operation start
            getattr(logger, log_level)(f"Starting {operation_name}")
            
            try:
                result = await func(*args, **kwargs)
                getattr(logger, log_level)(f"Completed {operation_name} successfully")
                return result
            except Exception as e:
                logger.error(f"Failed {operation_name}: {e}")
                raise
                
        return wrapper
    return decorator


def handle_endpoint_errors(operation_name: str, default_status_code: int = 500):
    """
    Decorator to handle common endpoint errors with consistent responses.
    
    Args:
        operation_name: Name of the operation for error messages
        default_status_code: Default HTTP status code for errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except ValueError as e:
                # Handle validation errors
                logger = logging.getLogger(func.__module__)
                logger.warning(f"{operation_name} validation failed: {e}")
                sanitized_error = UniversalValidator.sanitize_error_message(str(e))
                raise HTTPException(status_code=400, detail=f"Invalid input: {sanitized_error}")
            except Exception as e:
                # Handle all other errors
                logger = logging.getLogger(func.__module__)
                logger.error(f"{operation_name} failed: {e}")
                sanitized_error = UniversalValidator.sanitize_error_message(str(e))
                raise HTTPException(status_code=default_status_code, detail=f"Error in {operation_name}: {sanitized_error}")
                
        return wrapper
    return decorator


def log_and_handle_errors(operation_name: str, log_level: str = "info", default_status_code: int = 500):
    """
    Combined decorator for logging and error handling.
    
    Args:
        operation_name: Name of the operation
        log_level: Logging level for success cases
        default_status_code: Default HTTP status code for errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            
            # Log the operation start
            getattr(logger, log_level)(f"Starting {operation_name}")
            
            try:
                result = await func(*args, **kwargs)
                getattr(logger, log_level)(f"Completed {operation_name} successfully")
                return result
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except ValueError as e:
                # Handle validation errors
                logger.warning(f"{operation_name} validation failed: {e}")
                sanitized_error = UniversalValidator.sanitize_error_message(str(e))
                raise HTTPException(status_code=400, detail=f"Invalid input: {sanitized_error}")
            except Exception as e:
                # Handle all other errors
                logger.error(f"{operation_name} failed: {e}")
                sanitized_error = UniversalValidator.sanitize_error_message(str(e))
                raise HTTPException(status_code=default_status_code, detail=f"Error in {operation_name}: {sanitized_error}")
                
        return wrapper
    return decorator
