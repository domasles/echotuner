"""
Comprehensive validation system for EchoTuner API.
Provides unified validation with decorators and validators.
"""

import logging
import re

from typing import Callable, Any, Optional
from fastapi import HTTPException, Request
from pydantic import BaseModel
from functools import wraps

from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class UniversalValidator:
    """Enhanced universal validator with comprehensive validation methods."""

    # Configuration constants
    MAX_PLAYLIST_NAME_LENGTH = settings.MAX_PLAYLIST_NAME_LENGTH
    MAX_PROMPT_LENGTH = settings.MAX_PROMPT_LENGTH

    # Validation patterns
    PLAYLIST_NAME_PATTERN = re.compile(r'^[\w\s\-_.,!?()\u0080-\U0001F6FF]+$', re.UNICODE)

    # Security patterns
    DANGEROUS_PROMPT_PATTERNS = [
        r'<script.*?>.*?</script>', # Script tags
        r'javascript:',             # JavaScript protocol
        r'vbscript:',               # VBScript protocol
        r'data:text/html',          # Data URLs
        r'eval\s*\(',               # Eval calls
        r'exec\s*\(',               # Exec calls
        r'import\s+',               # Import statements
        r'__[a-zA-Z_]+__',          # Python dunder methods
        r'\.\./',                   # Directory traversal
        r'file://',                 # File protocol
    ]

    @classmethod
    def sanitize_error_message(cls, error_message: str) -> str:
        """Sanitize error messages to prevent information disclosure."""
        if not isinstance(error_message, str):
            return "Internal error occurred"
            
        sanitized = re.sub(r'/[a-zA-Z0-9_/.-]+', '[PATH]', error_message)
        sanitized = re.sub(r'[A-Za-z]:[\\a-zA-Z0-9_\\.-]+', '[PATH]', sanitized)
        sanitized = re.sub(r'line \d+', 'line [NUM]', sanitized)
        sanitized = re.sub(r'function \w+', 'function [NAME]', sanitized)
        sanitized = re.sub(r'<[^>]+>', '[INTERNAL]', sanitized)
        
        return sanitized

    @classmethod
    def validate_string(cls, value: Any, field_name: str, max_length: int, 
                       pattern: Optional[re.Pattern] = None, required: bool = True) -> str:
        """Universal string validation with security checks."""
        
        if value is None or value == "":
            if required:
                raise Exception(f"{field_name} must be provided")
            return ""

        if not isinstance(value, str):
            raise Exception(f"{field_name} must be a string")

        if len(value) > max_length:
            raise Exception(f"{field_name} exceeds maximum length of {max_length} characters")

        if pattern and not pattern.match(value):
            raise Exception(f"{field_name} contains invalid characters")

        return value.strip()

    @classmethod
    def validate_prompt(cls, prompt: str) -> str:
        """Validate and sanitize AI prompt input."""
        if not prompt or not isinstance(prompt, str):
            raise Exception("Prompt must be a non-empty string")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PROMPT_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise Exception("Prompt contains potentially dangerous content")

        return cls.validate_string(prompt, "prompt", cls.MAX_PROMPT_LENGTH)

    @classmethod
    def validate_json_context(cls, json_data: dict, max_size_bytes: int = 10240) -> dict:
        """Validate and sanitize JSON user context data."""
        import json
        
        if not isinstance(json_data, dict):
            raise Exception("User context must be a valid JSON object")
        
        # Convert to JSON string to check size
        json_str = json.dumps(json_data)
        if len(json_str.encode('utf-8')) > max_size_bytes:
            raise Exception(f"User context exceeds maximum size of {max_size_bytes} bytes")
        
        # Check for dangerous patterns in JSON values
        def sanitize_value(value):
            if isinstance(value, str):
                # Check for dangerous patterns
                for pattern in cls.DANGEROUS_PROMPT_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise Exception("User context contains potentially dangerous content")
                return value
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            else:
                return value
        
        return sanitize_value(json_data)

    @classmethod
    def validate_count(cls, count: int, min_count: int = 1, max_count: int = 100) -> int:
        """Validate count parameter."""
        if not isinstance(count, int):
            raise Exception("Count must be an integer")
        
        if count < min_count:
            raise Exception(f"Count must be at least {min_count}")
        
        if count > max_count:
            raise Exception(f"Count cannot exceed {max_count}")
        
        return count

    @classmethod
    def validate_playlist_name(cls, name: str) -> str:
        """Validate playlist name."""
        return cls.validate_string(name, "playlist_name", cls.MAX_PLAYLIST_NAME_LENGTH, cls.PLAYLIST_NAME_PATTERN)

    @classmethod
    def validate_ip_address(cls, ip_address: str) -> str:
        """Validate IP address format."""
        if not ip_address:
            raise Exception("IP address is required")

        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|'
            r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        )
        
        if not ip_pattern.match(ip_address):
            raise Exception("Invalid IP address format")
            
        return ip_address

def validate_user_request():
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
            logger.info(f"Extracted user_id: '{user_id}'")
            
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

def validate_request(*field_names: str):
    """
    Decorator for automatic request validation.
    
    Args:
        *field_names: Fields to validate (e.g., 'prompt', 'count')
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
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
