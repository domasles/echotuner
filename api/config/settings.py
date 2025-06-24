import os

from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings:
    """Configuration settings for EchoTuner API."""

    API_HOST: str = os.getenv("API_HOST", "localhost")
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

    DAILY_LIMIT_ENABLED: bool = os.getenv("DAILY_LIMIT_ENABLED", "false").lower() == "true"
    MAX_PLAYLISTS_PER_DAY: int = int(os.getenv("MAX_PLAYLISTS_PER_DAY", 3))
    MAX_SONGS_PER_PLAYLIST: int = int(os.getenv("MAX_SONGS_PER_PLAYLIST", 30))
    MAX_REFINEMENTS_PER_PLAYLIST: int = int(os.getenv("MAX_REFINEMENTS_PER_PLAYLIST", 3))

    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    LOGGER_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red',
        "EchoTuner": 'magenta'
    }

settings = Settings()
