"""
Comprehensive validation system for EchoTuner API.
Provides unified validation with decorators and validators.
"""

import logging
import re

from typing import Any, Optional
from pydantic import BaseModel

from domain.config.settings import settings

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

    @classmethod
    def validate_dict_against_template(cls, data: dict, validation_template: dict) -> dict:
        """
        Validate a dictionary against a validation template with __all__ type-based defaults.
        
        Args:
            data: Dictionary to validate
            validation_template: Dict with field validation rules
                Format: {
                    'field_name': {
                        'type': 'list'|'string'|'int',
                        'max_count': int (for lists),
                        'max_length': int (for strings/ints),
                    },
                    '__all__': {
                        'type': 'string'|'int'|'list',
                        'max_length': int (for strings/ints),
                        'max_count': int (for lists)
                    }
                }
        
        Returns:
            Validated and sanitized dictionary
        """
        
        validated_data = {}
        
        # Extract __all__ type-based defaults
        all_defaults = {}
        for field_name, rules in validation_template.items():
            if field_name == '__all__':
                # Handle nested structure: '__all__': {'string': {...}, 'int': {...}}
                if isinstance(rules, dict):
                    for type_name, type_rules in rules.items():
                        all_defaults[type_name] = type_rules
        
        # First, validate explicitly defined fields
        for field_name, rules in validation_template.items():
            if field_name == '__all__':
                continue
                
            field_value = data.get(field_name)
            
            # Skip validation if field is not provided
            if field_value is None:
                continue
            
            # Auto-detect field type and validate
            field_type = cls._determine_field_type(field_value)
            validated_data[field_name] = cls._validate_field_by_type(
                field_value, field_name, field_type, rules
            )
        
        # Then, validate remaining fields using __all__ defaults
        for field_name, field_value in data.items():
            if field_name in validation_template or field_name in validated_data:
                continue  # Already validated
                
            if field_value is None:
                continue
            
            # Auto-detect field type and apply __all__ rules
            field_type = cls._determine_field_type(field_value)
            
            if field_type in all_defaults:
                validated_data[field_name] = cls._validate_field_by_type(
                    field_value, field_name, field_type, all_defaults[field_type]
                )
            else:
                # No __all__ rule for this type, pass through
                validated_data[field_name] = field_value
        
        return validated_data

    @classmethod
    def _determine_field_type(cls, value: Any) -> str:
        """Determine the type of a field value."""
        if isinstance(value, list):
            return 'list'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, bool):
            return 'bool'
        else:
            return 'unknown'

    @classmethod
    def _validate_field_by_type(cls, field_value: Any, field_name: str, field_type: str, rules: dict) -> Any:
        """Validate a field based on its type and rules."""
        
        if field_type == 'list':
            if not isinstance(field_value, list):
                raise Exception(f"{field_name} must be a list")
            
            max_count = rules.get('max_count')
            if max_count and len(field_value) > max_count:
                raise Exception(f"{field_name} cannot contain more than {max_count} items")
            
            # Validate each item in the list is a string (for most use cases)
            validated_list = []
            for item in field_value:
                if isinstance(item, str):
                    validated_list.append(item.strip())
                else:
                    validated_list.append(item)
            
            return validated_list
            
        elif field_type == 'string':
            if not isinstance(field_value, str):
                raise Exception(f"{field_name} must be a string")
            
            max_length = rules.get('max_length', 1000)
            return cls.validate_string(field_value, field_name, max_length, required=False)
            
        elif field_type == 'int':
            if not isinstance(field_value, int):
                raise Exception(f"{field_name} must be an integer")
            
            # Check integer length (number of digits)
            max_length = rules.get('max_length')
            if max_length:
                int_str = str(abs(field_value))  # Remove negative sign for length check
                if len(int_str) > max_length:
                    raise Exception(f"{field_name} integer length cannot exceed {max_length} digits")
            
            return field_value
            
        else:
            # For unknown types, just pass through
            return field_value
