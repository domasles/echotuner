"""
Logging configuration for EchoTuner API.
"""

import logging
import sys

import click
from domain.config.app_constants import app_constants


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development - maintains original EchoTuner style"""

    def format(self, record: logging.LogRecord) -> str:
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

        return formatted_message


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging with original EchoTuner style"""

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Console handler with original EchoTuner formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleFormatter("%(levelname)s%(message)s"))

    root_logger.addHandler(console_handler)

    # Service-specific loggers
    service_loggers = [
        "services.ai_service",
        "services.auth_service",
        "services.database_service",
        "services.playlist_generator_service",
        "services.spotify_search_service",
        "core.service_manager",
    ]

    for logger_name in service_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)
