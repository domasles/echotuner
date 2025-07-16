"""
Comprehensive validation system for EchoTuner API.
Provides unified validation with decorators and validators.
"""

import re
import logging
from functools import wraps
from typing import Callable, Any, Optional, Union, List, Dict
from fastapi import HTTPException
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error for internal use"""
    pass

class UniversalValidator:
    """Enhanced universal validator with comprehensive validation methods."""

    # Configuration constants
    MAX_PLAYLIST_NAME_LENGTH = settings.MAX_PLAYLIST_NAME_LENGTH
    MAX_PROMPT_LENGTH = settings.MAX_PROMPT_LENGTH
    MAX_DEVICE_ID_LENGTH = 100
    MAX_SESSION_ID_LENGTH = 100

    # Validation patterns
    DEVICE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
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
                raise ValidationError(f"{field_name} must be provided")
            return ""

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")

        if len(value) > max_length:
            raise ValidationError(f"{field_name} exceeds maximum length of {max_length} characters")

        if pattern and not pattern.match(value):
            raise ValidationError(f"{field_name} contains invalid characters")

        return value.strip()

    @classmethod
    def validate_prompt(cls, prompt: str) -> str:
        """Validate and sanitize AI prompt input."""
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("Prompt must be a non-empty string")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PROMPT_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise ValidationError("Prompt contains potentially dangerous content")

        return cls.validate_string(prompt, "prompt", cls.MAX_PROMPT_LENGTH)

    @classmethod
    def validate_device_id(cls, device_id: str) -> str:
        """Validate device ID format."""
        return cls.validate_string(device_id, "device_id", cls.MAX_DEVICE_ID_LENGTH, cls.DEVICE_ID_PATTERN)

    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """Validate session ID format."""
        return cls.validate_string(session_id, "session_id", cls.MAX_SESSION_ID_LENGTH, cls.SESSION_ID_PATTERN)

    @classmethod
    def validate_count(cls, count: int, min_count: int = 1, max_count: int = 100) -> int:
        """Validate count parameter."""
        if not isinstance(count, int):
            raise ValidationError("Count must be an integer")
        
        if count < min_count:
            raise ValidationError(f"Count must be at least {min_count}")
        
        if count > max_count:
            raise ValidationError(f"Count cannot exceed {max_count}")
        
        return count

    @classmethod
    def validate_playlist_name(cls, name: str) -> str:
        """Validate playlist name."""
        return cls.validate_string(name, "playlist_name", cls.MAX_PLAYLIST_NAME_LENGTH, cls.PLAYLIST_NAME_PATTERN)

    @classmethod
    def validate_ip_address(cls, ip_address: str) -> str:
        """Validate IP address format."""
        if not ip_address:
            raise ValidationError("IP address is required")

        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|'
            r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        )
        
        if not ip_pattern.match(ip_address):
            raise ValidationError("Invalid IP address format")
            
        return ip_address


def validate_request(*field_names: str):
    """
    Decorator for automatic request validation.
    
    Args:
        *field_names: Fields to validate (e.g., 'prompt', 'device_id', 'session_id', 'count')
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
                        elif field_name == 'device_id' and field_value:
                            validated_data[field_name] = UniversalValidator.validate_device_id(field_value)
                        elif field_name == 'session_id' and field_value:
                            validated_data[field_name] = UniversalValidator.validate_session_id(field_value)
                        elif field_name == 'count' and field_value is not None:
                            validated_data[field_name] = UniversalValidator.validate_count(field_value)
                        elif field_name == 'playlist_name' and field_value:
                            validated_data[field_name] = UniversalValidator.validate_playlist_name(field_value)
                
                # Update request object with validated data
                for field_name, validated_value in validated_data.items():
                    setattr(request, field_name, validated_value)
                
            except ValidationError as e:
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
