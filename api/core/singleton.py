"""Singleton pattern implementation for EchoTuner services."""

import threading
import asyncio
import logging

from typing import Dict, Type, Any

logger = logging.getLogger(__name__)

class ServiceSingleton:
    """Thread-safe singleton metaclass for services."""

    _instances: Dict[Type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls not in ServiceSingleton._instances:
            with ServiceSingleton._lock:
                if cls not in ServiceSingleton._instances:
                    ServiceSingleton._instances[cls] = super(ServiceSingleton, cls).__new__(cls)

        return ServiceSingleton._instances[cls]


class SingletonServiceBase:
    """Base class for singleton services with managed logging."""

    def __init__(self):
        self._logger_name = self.__class__.__name__

        self._setup_service()
    
    def _setup_service(self):
        """Override this method to set up the service."""

        pass

    def _log_initialization(self, message: str, logger):
        """Log initialization only once per singleton instance."""

        logger.info(message)

    async def cleanup(self):
        """Clean up resources and shutdown the service."""

        logger.info("Service cleanup completed.")

    def __del__(self):
        """Cleanup resources on destruction"""

        asyncio.run(self.cleanup())
