"""Server-related endpoint implementations"""

import logging
from fastapi import APIRouter
from config.settings import settings
from core.service_manager import service_manager

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/server", tags=["server"])

@router.get("/mode")
async def get_server_mode():
    """Get current server mode"""

    return {
        "demo_mode": settings.DEMO,
        "mode": "demo" if settings.DEMO else "normal"
    }

@router.get("/health")
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
        "version": "1.3.0-beta"
    }
