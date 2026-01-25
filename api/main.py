import asyncio
import logging
import uvicorn
import re

from contextlib import asynccontextmanager

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

from application import *
from application.service_manager import service_manager

from domain.config.app_constants import app_constants
from domain.config.security import security
from domain.config.settings import settings

from infrastructure.rate_limiting.limit_service import rate_limiter_service
from infrastructure.personality.service import personality_service
from infrastructure.spotify.search_service import spotify_search_service
from infrastructure.filesystem.service import filesystem_service
from infrastructure.template.service import template_service
from infrastructure.logging.config import configure_logging
from infrastructure.ai.registry import provider_registry
from infrastructure.auth.service import oauth_service
from infrastructure.database.core import db_core

from domain.playlist.generator import playlist_generator_service
from infrastructure.spotify.playlist_service import spotify_playlist_service
from domain.playlist.draft import playlist_draft_service

from presentation.endpoints.personality import router as personality_router
from presentation.endpoints.config import router as config_router, root
from presentation.endpoints.playlist import router as playlist_router
from presentation.endpoints.server import router as server_router
from presentation.endpoints.user import router as user_router
from presentation.endpoints.auth import router as auth_router
from presentation.endpoints.ai import router as ai_router

configure_logging(level=settings.LOG_LEVEL)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""

    logger.info("Initializing EchoTuner API services...")

    try:
        service_manager.register_service("filesystem_service", filesystem_service)
        service_manager.register_service("rate_limiter_service", rate_limiter_service)
        service_manager.register_service("template_service", template_service)
        service_manager.register_service("ai_service", provider_registry)
        service_manager.register_service("spotify_search_service", spotify_search_service)
        service_manager.register_service("spotify_playlist_service", spotify_playlist_service)
        service_manager.register_service("playlist_generator_service", playlist_generator_service)
        service_manager.register_service("playlist_draft_service", playlist_draft_service)
        service_manager.register_service("personality_service", personality_service)
        service_manager.register_service("oauth_service", oauth_service)
        service_manager.register_service("database_core", db_core)

        await service_manager.initialize_all_services()
        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    logger.info("Shutting down EchoTuner API...")

    try:
        await service_manager.shutdown_all()
        logger.info("All services shut down successfully")

    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")


app = FastAPI(
    title=app_constants.API_TITLE,
    description="AI-powered playlist generation with real-time song search",
    version=app_constants.API_VERSION,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="templates"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to handle logging for endpoints"""

    response = await call_next(request)
    route = request.scope.get("route")

    if route and hasattr(route, "endpoint"):
        endpoint = route.endpoint

        if hasattr(endpoint, "_no_logging") and endpoint._no_logging:
            request.state.skip_logging = True

    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""

    response = await call_next(request)
    nonce = None

    if hasattr(response, "body") and b"nonce=" in response.body:
        body_str = response.body.decode("utf-8")
        nonce_match = re.search(r'nonce="([^"]+)"', body_str)

        if nonce_match:
            nonce = nonce_match.group(1)

    headers = security.get_security_headers(nonce)

    for header, value in headers.items():
        response.headers[header] = value

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(personality_router)
app.include_router(ai_router)
app.include_router(config_router)
app.include_router(server_router)
app.include_router(user_router)

app.get("/")(root)

if __name__ == "__main__":
    logger.info(app_constants.STARTUP_MESSAGE)

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
        reload_excludes=["__pycache__", "storage", "templates", ".git", ".github", "venv"],
    )
