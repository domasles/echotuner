import asyncio
import logging
import uvicorn
import click
import sys
import re

from contextlib import asynccontextmanager
from pathlib import Path

# FastAPI and middleware imports
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Application layer imports
from application import *
from application.service_manager import service_manager

# Infrastructure imports
from infrastructure.config.app_constants import app_constants
from infrastructure.config.security import security
from infrastructure.config.settings import settings
from infrastructure.logging.config import configure_logging

# Domain imports  
from domain.shared.validation.validators import UniversalValidator

# Service imports for registration
from infrastructure.filesystem.service import filesystem_service
from infrastructure.data.service import data_loader
from infrastructure.rate_limiting.limit_service import rate_limiter_service
from infrastructure.rate_limiting.ip_limit_service import ip_rate_limiter_service
from infrastructure.template.service import template_service
from domain.ai.service import ai_service
from infrastructure.spotify.service import spotify_search_service
from domain.playlist.spotify import spotify_playlist_service
from domain.playlist.generator import playlist_generator_service
from domain.playlist.draft import playlist_draft_service
from domain.personality.service import personality_service
from infrastructure.auth.oauth_service import oauth_service

# Router imports
from presentation.endpoints.auth import router as auth_router
from presentation.endpoints.playlist import router as playlist_router
from presentation.endpoints.personality import router as personality_router
from presentation.endpoints.ai import router as ai_router
from presentation.endpoints.config import router as config_router, root
from presentation.endpoints.server import router as server_router

# Configure structured logging early
configure_logging(
    level=settings.LOG_LEVEL,
    structured=settings.STRUCTURED_LOGGING
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    
    # Startup
    logger.info("Initializing EchoTuner API services...")
    
    try:
        # Register services with service manager
        service_manager.register_service("filesystem_service", filesystem_service)
        service_manager.register_service("data_service", data_loader)
        service_manager.register_service("rate_limiter_service", rate_limiter_service)
        service_manager.register_service("ip_rate_limiter_service", ip_rate_limiter_service)
        service_manager.register_service("template_service", template_service)
        service_manager.register_service("ai_service", ai_service)
        service_manager.register_service("spotify_search_service", spotify_search_service)
        service_manager.register_service("spotify_playlist_service", spotify_playlist_service)
        service_manager.register_service("playlist_generator_service", playlist_generator_service)
        service_manager.register_service("playlist_draft_service", playlist_draft_service)
        service_manager.register_service("personality_service", personality_service)
        service_manager.register_service("oauth_service", oauth_service)
        
        # Initialize all services
        await service_manager.initialize_all_services()
        
        # Initialize database explicitly during startup
        from infrastructure.database.core import db_core
        await db_core.initialize()

        # Pre-load data cache in background
        asyncio.create_task(preload_data_cache())
        
        logger.info("✓ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down EchoTuner API...")
    try:
        await service_manager.shutdown_all()
        logger.info("✓ All services shut down successfully")
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")

async def preload_data_cache():
    """Pre-load frequently used data in background"""
    
    try:
        loop = asyncio.get_event_loop()
        
        preload_tasks = [
            loop.run_in_executor(None, data_loader.get_mood_patterns),
            loop.run_in_executor(None, data_loader.get_genre_patterns),
            loop.run_in_executor(None, data_loader.get_activity_patterns),
            loop.run_in_executor(None, data_loader.get_energy_trigger_words),
        ]
        
        await asyncio.gather(*preload_tasks, return_exceptions=True)
        logger.info("Data cache preloaded successfully")
        
    except Exception as e:
        logger.warning(f"Cache preloading failed (non-critical): {e}")

app = FastAPI(
    title=app_constants.API_TITLE,
    description="AI-powered playlist generation with real-time song search",
    version=app_constants.API_VERSION,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="templates"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    nonce = None
    
    if hasattr(response, 'body') and b'nonce=' in response.body:
        body_str = response.body.decode('utf-8')
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

# Include all routers
app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(personality_router)
app.include_router(ai_router)
app.include_router(config_router)
app.include_router(server_router)

# Root endpoint - use the one from config.py
app.get("/")(root)

if __name__ == "__main__":
    logger.info(app_constants.STARTUP_MESSAGE)

    uvicorn.run(
        "main:app",

        host=settings.API_HOST,
        port=settings.API_PORT,

        log_level=settings.LOG_LEVEL.lower(),

        reload=settings.DEBUG,
        reload_excludes=["__pycache__", "storage", "templates", ".git", ".github", "venv"]
    )
