import sys
import os

from dotenv import load_dotenv
from typing import Optional
from pathlib import Path

api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

load_dotenv(f"{api_dir}/.env")

class Settings:
    """Configuration settings for EchoTuner API."""

    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "true").lower() == "true"
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", 30))
    OLLAMA_MODEL_PULL_TIMEOUT: int = int(os.getenv("OLLAMA_MODEL_PULL_TIMEOUT", 300))

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_VALIDATION_MODEL: str = os.getenv("OLLAMA_VALIDATION_MODEL", "nomic-embed-text:latest")
    OLLAMA_GENERATION_MODEL: str = os.getenv("OLLAMA_GENERATION_MODEL", "phi3:mini")

    PROMPT_VALIDATION_THRESHOLD: float = float(os.getenv("PROMPT_VALIDATION_THRESHOLD", 0.6))
    PROMPT_VALIDATION_TIMEOUT: int = int(os.getenv("PROMPT_VALIDATION_TIMEOUT", 30))
    
    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", f"http://{API_HOST}:{API_PORT}/auth/callback")

    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "true").lower() == "true"

    PLAYLIST_LIMIT_ENABLED: bool = os.getenv("PLAYLIST_LIMIT_ENABLED", "false").lower() == "true"
    REFINEMENT_LIMIT_ENABLED: bool = os.getenv("REFINEMENT_LIMIT_ENABLED", "false").lower() == "true"

    MAX_PLAYLISTS_PER_DAY: int = int(os.getenv("MAX_PLAYLISTS_PER_DAY", 3))
    MAX_SONGS_PER_PLAYLIST: int = int(os.getenv("MAX_SONGS_PER_PLAYLIST", 30))
    MAX_REFINEMENTS_PER_PLAYLIST: int = int(os.getenv("MAX_REFINEMENTS_PER_PLAYLIST", 3))

    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", 24))

    DRAFT_STORAGE_TIMEOUT: int = int(os.getenv("DRAFT_STORAGE_DAYS", 7))
    DRAFT_CLEANUP_INTERVAL: int = int(os.getenv("DRAFT_CLEANUP_INTERVAL_HOURS", 24))

    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    MAX_AUTH_ATTEMPTS_PER_IP: int = int(os.getenv("MAX_AUTH_ATTEMPTS_PER_IP", 10))
    AUTH_ATTEMPT_WINDOW_MINUTES: int = int(os.getenv("AUTH_ATTEMPT_WINDOW_MINUTES", 60))
    SECURE_HEADERS: bool = os.getenv("SECURE_HEADERS", "true").lower() == "true"

settings = Settings()
