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
    INPUT_INVALID = "VAL002"
    CONFIG_INVALID = "VAL003"
    
    # General errors
    INTERNAL_ERROR = "GEN001"
    EXTERNAL_SERVICE_ERROR = "GEN002"
    TIMEOUT_ERROR = "GEN003"
    RESOURCE_UNAVAILABLE = "GEN004"

class EchoTunerException(Exception):
    """Base exception class for all EchoTuner-specific exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
    
    def _get_default_user_message(self) -> str:
        """Get default user-friendly message based on error code."""
        user_messages = {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid credentials provided.",
            ErrorCode.AUTH_SESSION_EXPIRED: "Your session has expired. Please log in again.",
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: "You don't have permission to perform this action.",
            ErrorCode.AUTH_STATE_INVALID: "Authentication state is invalid.",
            
            ErrorCode.DB_CONNECTION_FAILED: "Database connection failed. Please try again.",
            ErrorCode.DB_OPERATION_FAILED: "Database operation failed. Please try again.",
            ErrorCode.DB_ENTITY_NOT_FOUND: "Requested item not found.",
            ErrorCode.DB_CONSTRAINT_VIOLATION: "Data validation failed.",
            
            ErrorCode.PLAYLIST_NOT_FOUND: "Playlist not found.",
            ErrorCode.PLAYLIST_CREATION_FAILED: "Failed to create playlist. Please try again.",
            ErrorCode.PLAYLIST_UPDATE_FAILED: "Failed to update playlist. Please try again.",
            ErrorCode.PLAYLIST_DRAFT_INVALID: "Playlist draft is invalid.",
            
            ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded. Please wait before trying again.",
            ErrorCode.RATE_LIMIT_CHECK_FAILED: "Rate limit check failed.",
            
            ErrorCode.AI_PROVIDER_UNAVAILABLE: "AI service is currently unavailable.",
            ErrorCode.AI_GENERATION_FAILED: "Failed to generate playlist. Please try again.",
            ErrorCode.AI_EMBEDDING_FAILED: "AI processing failed. Please try again.",
            ErrorCode.AI_RESPONSE_INVALID: "Invalid AI response received.",
            
            ErrorCode.SPOTIFY_AUTH_FAILED: "Spotify authentication failed.",
            ErrorCode.SPOTIFY_API_ERROR: "Spotify service error. Please try again.",
            ErrorCode.SPOTIFY_PLAYLIST_ERROR: "Failed to create Spotify playlist.",
            ErrorCode.SPOTIFY_SEARCH_ERROR: "Spotify search failed. Please try again.",
            
            ErrorCode.VALIDATION_FAILED: "Input validation failed.",
            ErrorCode.INPUT_INVALID: "Invalid input provided.",
            ErrorCode.CONFIG_INVALID: "Configuration is invalid.",
            
            ErrorCode.INTERNAL_ERROR: "An internal error occurred. Please try again.",
            ErrorCode.EXTERNAL_SERVICE_ERROR: "External service error. Please try again.",
            ErrorCode.TIMEOUT_ERROR: "Request timed out. Please try again.",
            ErrorCode.RESOURCE_UNAVAILABLE: "Resource is currently unavailable."
        }
        return user_messages.get(self.error_code, "An error occurred. Please try again.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error_code": self.error_code.value,
            "message": self.user_message,
            "details": self.details
        }

class AuthenticationError(EchoTunerException):
    """Authentication-related errors."""
    pass

class DatabaseError(EchoTunerException):
    """Database-related errors."""
    pass

class PlaylistError(EchoTunerException):
    """Playlist-related errors."""
    pass

class RateLimitError(EchoTunerException):
    """Rate limiting errors."""
    pass

class AIServiceError(EchoTunerException):
    """AI service errors."""
    pass

class SpotifyError(EchoTunerException):
    """Spotify integration errors."""
    pass

class ValidationError(EchoTunerException):
    """Validation errors."""
    pass

class ExternalServiceError(EchoTunerException):
    """External service errors."""
    pass

class ErrorHandler:
    """Centralized error handling and response formatting."""
    
    @staticmethod
    def log_error(
        exception: Union[Exception, EchoTunerException],
        context: Optional[Dict[str, Any]] = None,
        level: str = "error"
    ):
        """Log error with context information."""
        log_func = getattr(logger, level, logger.error)
        
        if isinstance(exception, EchoTunerException):
            log_data = {
                "error_code": exception.error_code.value,
                "message": exception.message,
                "details": exception.details
            }
        else:
            log_data = {
                "error_type": type(exception).__name__,
                "message": str(exception)
            }
        
        if context:
            log_data["context"] = context
        
        log_func(f"Error occurred: {log_data}")
    
    @staticmethod
    def create_http_exception(
        exception: Union[Exception, EchoTunerException],
        default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> HTTPException:
        """Create HTTPException from custom exception."""
        if isinstance(exception, EchoTunerException):
            status_code_map = {
                # Authentication errors
                ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
                ErrorCode.AUTH_SESSION_EXPIRED: status.HTTP_401_UNAUTHORIZED,
                ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
                ErrorCode.AUTH_STATE_INVALID: status.HTTP_400_BAD_REQUEST,
                
                # Database errors
                ErrorCode.DB_ENTITY_NOT_FOUND: status.HTTP_404_NOT_FOUND,
                ErrorCode.DB_CONSTRAINT_VIOLATION: status.HTTP_400_BAD_REQUEST,
                
                # Playlist errors
                ErrorCode.PLAYLIST_NOT_FOUND: status.HTTP_404_NOT_FOUND,
                ErrorCode.PLAYLIST_DRAFT_INVALID: status.HTTP_400_BAD_REQUEST,
                
                # Rate limiting errors
                ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
                
                # Validation errors
                ErrorCode.VALIDATION_FAILED: status.HTTP_400_BAD_REQUEST,
                ErrorCode.INPUT_INVALID: status.HTTP_400_BAD_REQUEST,
                ErrorCode.CONFIG_INVALID: status.HTTP_500_INTERNAL_SERVER_ERROR,
                
                # External service errors
                ErrorCode.SPOTIFY_AUTH_FAILED: status.HTTP_401_UNAUTHORIZED,
                ErrorCode.SPOTIFY_API_ERROR: status.HTTP_502_BAD_GATEWAY,
                ErrorCode.AI_PROVIDER_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
                ErrorCode.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
                ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
                ErrorCode.RESOURCE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE
            }
            
            status_code = status_code_map.get(exception.error_code, default_status_code)
            return HTTPException(status_code=status_code, detail=exception.to_dict())
        else:
            return HTTPException(status_code=default_status_code, detail=str(exception))
    
    @staticmethod
    def create_error_response(
        exception: Union[Exception, EchoTunerException],
        status_code: Optional[int] = None
    ) -> JSONResponse:
        """Create JSON error response."""
        if isinstance(exception, EchoTunerException):
            if status_code is None:
                http_exception = ErrorHandler.create_http_exception(exception)
                status_code = http_exception.status_code
            return JSONResponse(
                status_code=status_code,
                content=exception.to_dict()
            )
        else:
            return JSONResponse(
                status_code=status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error_code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "An internal error occurred. Please try again.",
                    "details": {}
                }
            )

def handle_service_errors(operation_name: str):
    """Decorator for handling service-level errors consistently."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except EchoTunerException:
                # Re-raise custom exceptions as-is
                raise
            except Exception as e:
                # Convert generic exceptions to custom format
                ErrorHandler.log_error(e, {"operation": operation_name})
                raise EchoTunerException(
                    message=f"Operation '{operation_name}' failed: {str(e)}",
                    error_code=ErrorCode.INTERNAL_ERROR,
                    details={"operation": operation_name, "original_error": str(e)}
                )
        return wrapper
    return decorator

# Convenience functions for common error scenarios
def raise_auth_error(message: str, error_code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS, **kwargs):
    """Raise authentication error."""
    raise AuthenticationError(message, error_code, **kwargs)

def raise_db_error(message: str, error_code: ErrorCode = ErrorCode.DB_OPERATION_FAILED, **kwargs):
    """Raise database error."""
    raise DatabaseError(message, error_code, **kwargs)

def raise_playlist_error(message: str, error_code: ErrorCode = ErrorCode.PLAYLIST_CREATION_FAILED, **kwargs):
    """Raise playlist error."""
    raise PlaylistError(message, error_code, **kwargs)

def raise_rate_limit_error(message: str, error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED, **kwargs):
    """Raise rate limit error."""
    raise RateLimitError(message, error_code, **kwargs)

def raise_ai_error(message: str, error_code: ErrorCode = ErrorCode.AI_GENERATION_FAILED, **kwargs):
    """Raise AI service error."""
    raise AIServiceError(message, error_code, **kwargs)

def raise_spotify_error(message: str, error_code: ErrorCode = ErrorCode.SPOTIFY_API_ERROR, **kwargs):
    """Raise Spotify error."""
    raise SpotifyError(message, error_code, **kwargs)

def raise_validation_error(message: str, error_code: ErrorCode = ErrorCode.VALIDATION_FAILED, **kwargs):
    """Raise validation error."""
    raise ValidationError(message, error_code, **kwargs)
