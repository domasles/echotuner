"""Server-related endpoint implementations"""

import logging
from config.settings import settings

logger = logging.getLogger(__name__)

async def get_server_mode():
    """Get current server mode"""

    return {
        "demo_mode": settings.DEMO,
        "mode": "demo" if settings.DEMO else "normal"
    }
