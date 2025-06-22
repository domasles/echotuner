from dotenv import load_dotenv
from typing import Optional
import os

load_dotenv()

class Settings:
    """Configuration settings for EchoTuner API."""

    API_HOST: str = os.getenv("API_HOST")
    API_PORT: int = int(os.getenv("API_PORT"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    OLLAMA_VALIDATION_MODEL: str = os.getenv("OLLAMA_VALIDATION_MODEL")
    OLLAMA_GENERATION_MODEL: str = os.getenv("OLLAMA_GENERATION_MODEL")

    USE_OLLAMA: bool = os.getenv("USE_OLLAMA").lower() == "true"

    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")

    DAILY_LIMIT_ENABLED: bool = os.getenv("DAILY_LIMIT_ENABLED").lower() == "true"
    MAX_PLAYLISTS_PER_DAY: int = int(os.getenv("MAX_PLAYLISTS_PER_DAY"))
    MAX_REFINEMENTS_PER_PLAYLIST: int = int(os.getenv("MAX_REFINEMENTS_PER_PLAYLIST"))

    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_spotify_credentials(cls) -> bool:
        """Check if Spotify credentials are properly configured"""

        return bool(cls.SPOTIFY_CLIENT_ID and cls.SPOTIFY_CLIENT_SECRET)
    
    @classmethod
    def get_ollama_timeout(cls) -> int:
        """Get Ollama request timeout in seconds"""

        return int(os.getenv("OLLAMA_TIMEOUT", "30"))

settings = Settings()
