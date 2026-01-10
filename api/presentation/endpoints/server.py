"""Server-related endpoint implementations"""

import logging

from domain.auth.decorators import debug_only
from fastapi import APIRouter

from domain.config.app_constants import app_constants
from domain.config.settings import settings

from application.service_manager import service_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/server", tags=["server"])


@router.get("/mode")
async def get_server_mode():
    """Get current server mode"""

    return {"shared_mode": settings.SHARED, "mode": "shared" if settings.SHARED else "normal"}
