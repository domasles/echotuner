"""Singleton pattern implementation for EchoTuner services."""

import logging

logger = logging.getLogger(__name__)

class SingletonServiceBase:
    """Base class for singleton services with managed logging."""

    def __init__(self):
        self._logger_name = self.__class__.__name__

    async def _setup_service(self):
        """Override this method to set up the service."""
        pass

    def cleanup(self):
        """Clean up resources and shutdown the service."""
        logger.info("Service cleanup completed.")

    def __del__(self):
        """Cleanup resources on destruction"""
        self.cleanup()
