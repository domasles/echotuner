"""
Centralized exception handling and custom exception hierarchy.
Provides consistent error handling across all services.
"""

import logging
from typing import Dict, Any, Optional, Union
from enum import Enum
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Standard error codes for the application."""
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH001"
    AUTH_SESSION_EXPIRED = "AUTH002"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH003"
    AUTH_STATE_INVALID = "AUTH004"
    
    # Database errors
    DB_CONNECTION_FAILED = "DB001"
    DB_OPERATION_FAILED = "DB002"
    DB_ENTITY_NOT_FOUND = "DB003"
    DB_CONSTRAINT_VIOLATION = "DB004"
    
    # Playlist errors
    PLAYLIST_NOT_FOUND = "PL001"
    PLAYLIST_CREATION_FAILED = "PL002"
    PLAYLIST_UPDATE_FAILED = "PL003"
    PLAYLIST_DRAFT_INVALID = "PL004"
    
    # Rate limiting errors
    RATE_LIMIT_EXCEEDED = "RL001"
    RATE_LIMIT_CHECK_FAILED = "RL002"
    
    # AI service errors
    AI_PROVIDER_UNAVAILABLE = "AI001"
    AI_GENERATION_FAILED = "AI002"
    AI_EMBEDDING_FAILED = "AI003"
    AI_RESPONSE_INVALID = "AI004"
    
    # Spotify errors
    SPOTIFY_AUTH_FAILED = "SP001"
    SPOTIFY_API_ERROR = "SP002"
    SPOTIFY_PLAYLIST_ERROR = "SP003"
    SPOTIFY_SEARCH_ERROR = "SP004"
    
    # Validation errors
    VALIDATION_FAILED = "VAL001"
    VALIDATION_INVALID_INPUT = "VAL002"
    VALIDATION_MISSING_FIELD = "VAL003"
    
    # Generic errors
    INTERNAL_ERROR = "INT001"
    OPERATION_FAILED = "OPR001"
    CONFIGURATION_ERROR = "CFG001"
    EXTERNAL_SERVICE_ERROR = "EXT001"

class EchoTunerException(Exception):
    """Base exception for all EchoTuner custom exceptions."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR, 
                 details: Optional[Dict[str, Any]] = None, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

class AuthenticationError(EchoTunerException):
    """Authentication and authorization errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_401_UNAUTHORIZED)

class DatabaseError(EchoTunerException):
    """Database operation errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DB_OPERATION_FAILED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_500_INTERNAL_SERVER_ERROR)

class OperationFailedError(EchoTunerException):
    """Generic operation failure."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.OPERATION_FAILED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_500_INTERNAL_SERVER_ERROR)

class ValidationError(EchoTunerException):
    """Input validation errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.VALIDATION_FAILED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_400_BAD_REQUEST)

class RateLimitError(EchoTunerException):
    """Rate limiting errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_429_TOO_MANY_REQUESTS)

class AIServiceError(EchoTunerException):
    """AI service errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AI_GENERATION_FAILED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_503_SERVICE_UNAVAILABLE)

class SpotifyError(EchoTunerException):
    """Spotify API errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SPOTIFY_API_ERROR, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_503_SERVICE_UNAVAILABLE)

class PlaylistError(EchoTunerException):
    """Playlist operation errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.PLAYLIST_CREATION_FAILED, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status.HTTP_500_INTERNAL_SERVER_ERROR)

# Convenience functions for common error scenarios
def raise_auth_error(message: str, error_code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS, **kwargs):
    """Raise authentication error."""
    raise AuthenticationError(message, error_code, **kwargs)

def raise_db_error(message: str, error_code: ErrorCode = ErrorCode.DB_OPERATION_FAILED, **kwargs):
    """Raise database error."""
    raise DatabaseError(message, error_code, **kwargs)

def raise_validation_error(message: str, error_code: ErrorCode = ErrorCode.VALIDATION_FAILED, **kwargs):
    """Raise validation error."""
    raise ValidationError(message, error_code, **kwargs)
