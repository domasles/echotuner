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
