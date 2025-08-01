"""
Service Manager.
Centralized service initialization and dependency management.
"""

import logging
from typing import Dict, Any

from infrastructure.singleton import SingletonServiceBase

logger = logging.getLogger(__name__)

class ServiceManager(SingletonServiceBase):
    """Manages service initialization order and dependencies"""

    def __init__(self):
        self.services = {}

    def register_service(self, name: str, service: Any):
        """Register a service for managed initialization"""

        self.services[name] = service
        logger.debug(f"Registered service: {name}")

    async def initialize_all_services(self):
        """Initialize all registered services in dependency order"""
        
        logger.info("Starting managed service initialization...")
        successful_services = []

        for service_name, service in self.services.items(): 
            try:
                service = self.services[service_name]

                await service._setup_service()

                successful_services.append(service_name)
                logger.info(f"{service_name} initialized successfully")
                    
            except Exception as e:
                logger.error(f"Failed to initialize {service_name}: {e}")

        logger.info(f"Service initialization complete. Success: {len(successful_services)}/{len(self.services)}")

    async def shutdown_all(self) -> Dict[str, bool]:
        """Shutdown all registered services"""

        logger.info("Starting managed service shutdown...")
        results = {}
        
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'close'):
                    logger.info(f"Shutting down {service_name}...")
                    await service.close()
                    results[service_name] = True
                    logger.info(f"{service_name} shut down successfully")
                else:
                    results[service_name] = True  # No cleanup needed
                    
            except Exception as e:
                logger.error(f"Failed to shutdown {service_name}: {e}")
                results[service_name] = False
                
        logger.info("Service shutdown complete")
        return results

service_manager = ServiceManager()
