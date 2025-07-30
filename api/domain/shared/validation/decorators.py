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
            user_id = request.headers.get('X-User-ID') or request.headers.get('x-user-id')
            logger.debug(f"Extracted user_id: '{user_id}'")
            
            if not user_id:
                logger.error("VALIDATOR: Missing X-User-ID header")
                raise HTTPException(status_code=422, detail="Missing X-User-ID header")
            
            # Validate user_id format (should be spotify_{id} or google_{id})
            if not (user_id.startswith('spotify_') or user_id.startswith('google_')):
                logger.error(f"VALIDATOR: Invalid X-User-ID format: '{user_id}'")
                raise HTTPException(status_code=422, detail="Invalid X-User-ID format")
            
            # Add validated user_id to kwargs for the endpoint function
            kwargs['validated_user_id'] = user_id
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def validate_request_data(*input_fields: str):
    """
    Decorator for automatic request validation of model fields.
    
    Args:
        input_fields: List of fields to validate from request model
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from domain.shared.validation.validators import UniversalValidator
            
            # Default fields to validate if none specified
            field_names = input_fields or ['prompt', 'count', 'playlist_name']
            
            # Find the request object in args
            request = None
            for arg in args:
                if hasattr(arg, '__class__') and issubclass(arg.__class__, BaseModel):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Validate each requested field
            validated_data = {}
            
            try:
                for field_name in field_names:
                    if hasattr(request, field_name):
                        field_value = getattr(request, field_name)
                        
                        if field_name == 'prompt' and field_value:
                            validated_data[field_name] = UniversalValidator.validate_prompt(field_value)
                        elif field_name == 'count' and field_value is not None:
                            validated_data[field_name] = UniversalValidator.validate_count(field_value)
                        elif field_name == 'playlist_name' and field_value:
                            validated_data[field_name] = UniversalValidator.validate_playlist_name(field_value)
                
                # Update request object with validated data
                for field_name, validated_value in validated_data.items():
                    setattr(request, field_name, validated_value)
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input(input_type: str = "general"):
    """
    Decorator for specific input type validation.
    
    Args:
        input_type: Type of input to validate
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This can be extended for specific input types
            return await func(*args, **kwargs)
        return wrapper
    return decorator


