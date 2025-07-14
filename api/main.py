import asyncio
import logging
import uvicorn
import click
import sys
import re

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

from contextlib import asynccontextmanager
from pathlib import Path

from models import *

from config.app_constants import app_constants
from config.security import security_config
from config.settings import settings
from utils.input_validator import UniversalValidator

# Core services
from core.service_manager import service_manager
from core.logging_config import configure_logging

# Service imports for registration
from services.filesystem_service import filesystem_service
from services.database_service import db_service
from services.embedding_cache_service import embedding_cache_service
from services.data_service import data_loader
from services.rate_limiter_service import rate_limiter_service
from services.ip_rate_limiter import ip_rate_limiter_service
from services.template_service import template_service
from services.ai_service import ai_service
from services.prompt_validator_service import prompt_validator_service
from services.spotify_search_service import spotify_search_service
from services.spotify_playlist_service import spotify_playlist_service
from services.playlist_generator_service import playlist_generator_service
from services.playlist_draft_service import playlist_draft_service
from services.personality_service import personality_service
from services.auth_service import auth_service
from utils.decorators import *

# Import routers
from endpoints.auth import router as auth_router
from endpoints.playlists import router as playlist_router
from endpoints.spotify import router as spotify_router
from endpoints.personality import router as personality_router
from endpoints.ai import router as ai_router
from endpoints.config import router as config_router, root
from endpoints.server import router as server_router

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
        service_manager.register_service("database_service", db_service)
        service_manager.register_service("embedding_cache_service", embedding_cache_service)
        service_manager.register_service("data_service", data_loader)
        service_manager.register_service("rate_limiter_service", rate_limiter_service)
        service_manager.register_service("ip_rate_limiter_service", ip_rate_limiter_service)
        service_manager.register_service("template_service", template_service)
        service_manager.register_service("ai_service", ai_service)
        service_manager.register_service("prompt_validator_service", prompt_validator_service)
        service_manager.register_service("spotify_search_service", spotify_search_service)
        service_manager.register_service("spotify_playlist_service", spotify_playlist_service)
        service_manager.register_service("playlist_generator_service", playlist_generator_service)
        service_manager.register_service("playlist_draft_service", playlist_draft_service)
        service_manager.register_service("personality_service", personality_service)
        service_manager.register_service("auth_service", auth_service)
        
        # Initialize all services
        await service_manager.initialize_all_services()
        
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
    
    headers = security_config.get_security_headers(nonce)
    
    for header, value in headers.items():
        response.headers[header] = value
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,
)

# Include all routers
app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(spotify_router)
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
        reload_excludes=["__pycache__", "storage", "templates", ".cache"]
    )
