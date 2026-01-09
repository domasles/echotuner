import sys
import os

from dotenv import load_dotenv
from typing import Optional
from pathlib import Path
from json import loads

api_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(api_dir))

load_dotenv(f"{api_dir}/.env")

class Settings:
    """Configuration settings for EchoTuner API."""

    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))

    SHARED: bool = os.getenv("SHARED", "false").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    STRUCTURED_LOGGING: bool = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"

    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")

    AI_ENDPOINT: str = os.getenv("AI_ENDPOINT", "http://localhost:11434")
    AI_GENERATION_MODEL: str = os.getenv("AI_GENERATION_MODEL", "phi3:mini")
    AI_MAX_TOKENS: Optional[int] = int(os.getenv("AI_MAX_TOKENS", 2000))
    AI_TEMPERATURE: Optional[float] = float(os.getenv("AI_TEMPERATURE", 0.7))
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", 30))

    CLOUD_API_KEY: Optional[str] = os.getenv("CLOUD_API_KEY")

    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", f"http://127.0.0.1:{API_PORT}/auth/spotify/callback")

    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", f"http://127.0.0.1:{API_PORT}/auth/google/callback")

    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "true").lower() == "true"
    SECURE_HEADERS: bool = os.getenv("SECURE_HEADERS", "true").lower() == "true"

    CORS_ORIGINS: list[str] = loads(os.getenv("CORS_ORIGINS", '["*"]'))

    PLAYLIST_LIMIT_ENABLED: bool = os.getenv("PLAYLIST_LIMIT_ENABLED", "false").lower() == "true"
    MAX_PLAYLISTS_PER_DAY: int = int(os.getenv("MAX_PLAYLISTS_PER_DAY", 3))
    MAX_SONGS_PER_PLAYLIST: int = int(os.getenv("MAX_SONGS_PER_PLAYLIST", 30))

    MAX_FAVORITE_ARTISTS: int = int(os.getenv("MAX_FAVORITE_ARTISTS", 12))
    MAX_DISLIKED_ARTISTS: int = int(os.getenv("MAX_DISLIKED_ARTISTS", 20))
    MAX_FAVORITE_GENRES: int = int(os.getenv("MAX_FAVORITE_GENRES", 10))
    MAX_PREFERRED_DECADES: int = int(os.getenv("MAX_PREFERRED_DECADES", 5))

    MAX_PROMPT_LENGTH: int = int(os.getenv("MAX_PROMPT_LENGTH", 128))
    MAX_PLAYLIST_NAME_LENGTH: int = int(os.getenv("MAX_PLAYLIST_NAME_LENGTH", 100))
        
settings = Settings()
