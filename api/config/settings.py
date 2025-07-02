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

    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "ollama")

    AI_ENDPOINT: str = os.getenv("AI_ENDPOINT", "http://localhost:11434")
    AI_GENERATION_MODEL: str = os.getenv("AI_GENERATION_MODEL", "phi3:mini")
    AI_EMBEDDING_MODEL: str = os.getenv("AI_EMBEDDING_MODEL", "nomic-embed-text:latest")
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", 30))
    AI_MODEL_PULL_TIMEOUT: int = int(os.getenv("AI_MODEL_PULL_TIMEOUT", 300))

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

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

    DRAFT_STORAGE_TIMEOUT: int = int(os.getenv("DRAFT_STORAGE_TIMEOUT", 7))
    DRAFT_CLEANUP_INTERVAL: int = int(os.getenv("DRAFT_CLEANUP_INTERVAL", 24))

    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    MAX_FAVORITE_ARTISTS: int = int(os.getenv("MAX_FAVORITE_ARTISTS", 12))
    MAX_DISLIKED_ARTISTS: int = int(os.getenv("MAX_DISLIKED_ARTISTS", 20))
    MAX_FAVORITE_GENRES: int = int(os.getenv("MAX_FAVORITE_GENRES", 10))
    MAX_PREFERRED_DECADES: int = int(os.getenv("MAX_PREFERRED_DECADES", 5))

    MAX_AUTH_ATTEMPTS_PER_IP: int = int(os.getenv("MAX_AUTH_ATTEMPTS_PER_IP", 10))
    AUTH_ATTEMPT_WINDOW_MINUTES: int = int(os.getenv("AUTH_ATTEMPT_WINDOW_MINUTES", 60))
    SECURE_HEADERS: bool = os.getenv("SECURE_HEADERS", "true").lower() == "true"

    MAX_PROMPT_LENGTH: int = int(os.getenv("MAX_PROMPT_LENGTH", 500))
    MAX_PLAYLIST_NAME_LENGTH: int = int(os.getenv("MAX_PLAYLIST_NAME_LENGTH", 100))
    
    # Demo Mode
    DEMO: bool = os.getenv("DEMO", "false").lower() == "true"
    
    def validate_required_settings(self) -> list[str]:
        """Validate that required settings are configured for production"""

        errors = []

        if not self.DEBUG:
            if not self.SPOTIFY_CLIENT_ID:
                errors.append("SPOTIFY_CLIENT_ID is required")

            if not self.SPOTIFY_CLIENT_SECRET:
                errors.append("SPOTIFY_CLIENT_SECRET is required")

            if not self.SPOTIFY_REDIRECT_URI:
                errors.append("SPOTIFY_REDIRECT_URI is required")

            if not self.SECURE_HEADERS:
                errors.append("SECURE_HEADERS should be enabled in production")

            if not self.AUTH_REQUIRED:
                errors.append("AUTH_REQUIRED should be enabled in production")

        
        return errors
        
settings = Settings()
