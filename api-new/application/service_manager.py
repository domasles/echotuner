"""
Service Manager.
Centralized service initialization and dependency management.
"""

import logging
from typing import Dict, Any

from application.core.singleton import SingletonServiceBase

logger = logging.getLogger(__name__)

class ServiceManager(SingletonServiceBase):
    """Manages service initialization order and dependencies"""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the service manager."""
        self.services: Dict[str, Any] = {}
        self.initialization_order = [
            # Filesystem service must be first to ensure directories exist
            'filesystem_service',
            
            # Core infrastructure services (no dependencies)
            'database_service',
            'data_service',
            
            # Core business services (minimal dependencies)
            'rate_limiter_service',
            'ip_rate_limiter_service',
            'template_service',
            
            # AI/ML services (depend on core services)
            'ai_service',
            
            # Business logic services (depend on AI services)
            'spotify_search_service',
            'spotify_playlist_service',
            'playlist_generator_service',
            'playlist_draft_service',
            'personality_service',
            
            # Authentication services (depend on database)
            'oauth_service'
        ]
        
        self._log_initialization("Service manager initialized successfully", logger)

    def register_service(self, name: str, service: Any):
        """Register a service for managed initialization"""

        self.services[name] = service
        logger.debug(f"Registered service: {name}")

    async def initialize_all_services(self) -> Dict[str, bool]:
        """Initialize all registered services in dependency order"""
        
        logger.info("Starting managed service initialization...")
        results = {}
        successful_services = []
        
        for service_name in self.initialization_order:
            if service_name not in self.services:
                logger.debug(f"Service {service_name} not registered, skipping")
                continue
                
            try:
                service = self.services[service_name]
                
                if hasattr(service, 'initialize'):
                    logger.info(f"Initializing {service_name}...")
                    await service.initialize()
                    results[service_name] = True
                    successful_services.append(service_name)
                    logger.info(f"{service_name} initialized successfully")

                else:
                    logger.debug(f"Service {service_name} requires no initialization")
                    results[service_name] = True
                    successful_services.append(service_name)
                    
            except Exception as e:
                logger.error(f"Failed to initialize {service_name}: {e}")
                results[service_name] = False
                
        logger.info(f"Service initialization complete. Success: {len(successful_services)}/{len([s for s in self.initialization_order if s in self.services])}")
        
        return results

    async def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered services"""

        status = {}
        
        for name, service in self.services.items():
            service_status = {
                'registered': True,
                'has_initialize': hasattr(service, 'initialize'),
                'is_singleton': isinstance(service, SingletonServiceBase),
                'class_name': service.__class__.__name__
            }
            
            # Check if service has a health check method
            if hasattr(service, 'is_ready'):
                try:
                    service_status['is_ready'] = service.is_ready()
                except:
                    service_status['is_ready'] = False
            
            status[name] = service_status
            
        return status

    async def shutdown_all(self) -> Dict[str, bool]:
        """Shutdown all registered services in reverse order"""

        logger.info("Starting managed service shutdown...")
        results = {}
        shutdown_order = list(reversed(self.initialization_order))
        
        for service_name in shutdown_order:
            if service_name not in self.services:
                continue
                
            try:
                service = self.services[service_name]
                
                if hasattr(service, 'close'):
                    logger.info(f"Shutting down {service_name}...")
                    await service.close()
                    results[service_name] = True
                    logger.info(f"{service_name} shutdown successfully")
                else:
                    logger.debug(f"Service {service_name} requires no shutdown")
                    results[service_name] = True
                    
            except Exception as e:
                logger.error(f"Failed to shutdown {service_name}: {e}")
                results[service_name] = False
                
        logger.info("Service shutdown complete")
        return results

service_manager = ServiceManager()
