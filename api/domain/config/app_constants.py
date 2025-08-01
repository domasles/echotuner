"""
Application constants for EchoTuner API.
Centralized constants for app name, version, colors, and other static values.
"""

class AppConstants:
    """Centralized application constants."""

    API_NAME = "EchoTuner"
    API_TITLE = "EchoTuner API"
    API_VERSION = "2.0.0-beta"

    DATABASE_FILEPATH = "storage/echotuner.db"
    SPOTIFY_CACHE_PATH = "storage/spotify_token_cache.json"

    REQUIRED_DIRECTORIES = ["storage"]

    DEFAULT_PLAYLIST_DESCRIPTION = "Generated by EchoTuner AI"
    API_WELCOME_MESSAGE = "EchoTuner API"
    STARTUP_MESSAGE = "EchoTuner API - AI-Powered Playlist Generation"

    SPOTIFY_SCOPE = "user-read-private user-read-email user-follow-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"

    LOGGER_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red',
        API_NAME: 'magenta'
    }

app_constants = AppConstants()
