"""Server-related endpoint implementations"""

import logging
from fastapi import APIRouter
from domain.auth.decorators import debug_only

from infrastructure.config.settings import settings
from application.service_manager import service_manager

from infrastructure.config.app_constants import app_constants

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/server", tags=["server"])

@router.get("/mode")
async def get_server_mode():
    """Get current server mode"""

    return {
        "shared_mode": settings.SHARED,
        "mode": "shared" if settings.SHARED else "normal"
    }

@router.get("/health")
@debug_only
async def health_check():
    """Health check endpoint with service status"""
    
    service_status = await service_manager.get_service_status()
    
    healthy_services = sum(1 for status in service_status.values() 
                          if status.get('is_ready', True))
    total_services = len(service_status)
    
    return {
        "status": "healthy" if healthy_services == total_services else "degraded",
        "services": {
            "healthy": healthy_services,
            "total": total_services,
            "details": service_status
        },
        "version": app_constants.API_VERSION
    }
