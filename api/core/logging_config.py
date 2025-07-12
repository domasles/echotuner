"""
Structured logging configuration for EchoTuner API.
Provides JSON-structured logging with proper formatting and context.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import click
from config.app_constants import app_constants

class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry, ensure_ascii=False)

class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development - maintains original EchoTuner style"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Preserve original record for structured logging
        original_levelname = record.levelname
        
        # Apply original EchoTuner color formatting
        raw_level = record.levelname
        color = app_constants.LOGGER_COLORS.get(raw_level, None)
        colored_level = click.style(raw_level, fg=color) if color else raw_level
        
        target_width = 10
        level_label_len = len(raw_level) + 1
        spaces = " " * max(0, target_width - level_label_len)
        
        record.levelname = f"{colored_level}:{spaces}"
        
        # Format the message using the original pattern
        formatted_message = super().format(record)
        
        # Restore original levelname for other handlers
        record.levelname = original_levelname
        
        return formatted_message

class StructuredLogger:
    """Wrapper for structured logging with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log_with_context(self, level: int, message: str, **context):
        """Log with additional context fields"""
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.extra_fields = context
        self.logger.handle(record)
        
    def debug(self, message: str, **context):
        self._log_with_context(logging.DEBUG, message, **context)
        
    def info(self, message: str, **context):
        self._log_with_context(logging.INFO, message, **context)
        
    def warning(self, message: str, **context):
        self._log_with_context(logging.WARNING, message, **context)
        
    def error(self, message: str, **context):
        self._log_with_context(logging.ERROR, message, **context)
        
    def critical(self, message: str, **context):
        self._log_with_context(logging.CRITICAL, message, **context)

def configure_logging(
    level: str = "INFO", 
    structured: bool = False,
    log_file: Optional[str] = None
) -> None:
    """Configure application logging with original EchoTuner style"""
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Console handler with original EchoTuner formatting
    console_handler = logging.StreamHandler(sys.stdout)
    
    if structured:
        # Use structured logging for production
        console_handler.setFormatter(StructuredFormatter())
    else:
        # Use original EchoTuner colored format for development
        console_handler.setFormatter(ConsoleFormatter('%(levelname)s%(message)s'))
        
    root_logger.addHandler(console_handler)
    
    # File handler if specified (always structured)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
    # Service-specific loggers
    service_loggers = [
        'services.ai_service',
        'services.auth_service', 
        'services.database_service',
        'services.embedding_cache_service',
        'services.playlist_generator_service',
        'services.prompt_validator_service',
        'services.spotify_search_service',
        'core.service_manager'
    ]
    
    for logger_name in service_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)

def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)
