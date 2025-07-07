"""
Input validation and sanitization utilities for enhanced security.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class InputValidator:
    """Validates and sanitizes user inputs for security."""

    MAX_PROMPT_LENGTH = 2000
    MAX_DEVICE_ID_LENGTH = 100
    MAX_SESSION_ID_LENGTH = 100
    MAX_PLAYLIST_NAME_LENGTH = 100

    DEVICE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    PLAYLIST_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$')

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
    def validate_prompt(cls, prompt: str) -> str:
        """Validate and sanitize AI prompt input."""

        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            raise ValueError(f"Prompt exceeds maximum length of {cls.MAX_PROMPT_LENGTH} characters")

        for pattern in cls.DANGEROUS_PROMPT_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in prompt: {pattern}")
                raise ValueError("Prompt contains potentially dangerous content")

        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', prompt)
        sanitized = re.sub(r'\s{5,}', ' ', sanitized)

        return sanitized.strip()
    
    @classmethod
    def validate_device_id(cls, device_id: str) -> str:
        """Validate device ID format."""

        if not device_id or not isinstance(device_id, str):
            raise ValueError("Device ID must be a non-empty string")

        if len(device_id) > cls.MAX_DEVICE_ID_LENGTH:
            raise ValueError(f"Device ID exceeds maximum length of {cls.MAX_DEVICE_ID_LENGTH} characters")

        if not cls.DEVICE_ID_PATTERN.match(device_id):
            raise ValueError("Device ID contains invalid characters")

        return device_id

    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """Validate session ID format."""

        if not session_id or not isinstance(session_id, str):
            raise ValueError("Session ID must be a non-empty string")

        if len(session_id) > cls.MAX_SESSION_ID_LENGTH:
            raise ValueError(f"Session ID exceeds maximum length of {cls.MAX_SESSION_ID_LENGTH} characters")

        if not cls.SESSION_ID_PATTERN.match(session_id):
            raise ValueError("Session ID contains invalid characters")

        return session_id

    @classmethod
    def validate_playlist_name(cls, name: str) -> str:
        """Validate playlist name."""

        if not name or not isinstance(name, str):
            raise ValueError("Playlist name must be a non-empty string")

        if len(name) > cls.MAX_PLAYLIST_NAME_LENGTH:
            raise ValueError(f"Playlist name exceeds maximum length of {cls.MAX_PLAYLIST_NAME_LENGTH} characters")

        if not cls.PLAYLIST_NAME_PATTERN.match(name):
            raise ValueError("Playlist name contains invalid characters")

        return name.strip()

    @classmethod
    def validate_count(cls, count: int, min_count: int = 1, max_count: int = 100) -> int:
        """Validate numeric count parameters."""

        if not isinstance(count, int):
            raise ValueError("Count must be an integer")

        if count < min_count or count > max_count:
            raise ValueError(f"Count must be between {min_count} and {max_count}")

        return count

    @classmethod
    def sanitize_error_message(cls, error_message: str) -> str:
        """Sanitize error messages to prevent information disclosure."""

        sanitized = re.sub(r'/[a-zA-Z0-9_/.-]+', '[PATH]', error_message)
        sanitized = re.sub(r'[A-Za-z]:[\\a-zA-Z0-9_\\.-]+', '[PATH]', sanitized)
        sanitized = re.sub(r'line \d+', 'line [NUM]', sanitized)
        sanitized = re.sub(r'function \w+', 'function [NAME]', sanitized)
        sanitized = re.sub(r'<[^>]+>', '[INTERNAL]', sanitized)
        
        return sanitized
