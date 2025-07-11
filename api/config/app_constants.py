"""
Application constants for EchoTuner API.
Centralized constants for app name, version, colors, and other static values.
"""

class AppConstants:
    """Centralized application constants."""

    API_NAME = "EchoTuner"
    API_TITLE = "EchoTuner API"
    API_VERSION = "1.1.0-beta"

    DATABASE_FILEPATH = "storage/echotuner.db"

    DEFAULT_PLAYLIST_DESCRIPTION = "Generated by EchoTuner AI"
    API_WELCOME_MESSAGE = "EchoTuner API"
    STARTUP_MESSAGE = "EchoTuner API - AI-Powered Playlist Generation"

    SPOTIFY_PLAYLISTS_TABLE = "echotuner_spotify_playlists"
    SPOTIFY_PLAYLISTS_USER_INDEX = "idx_echotuner_spotify_playlists_user_id"
    SPOTIFY_PLAYLISTS_DEVICE_INDEX = "idx_echotuner_spotify_playlists_device_id"

    LOGGER_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red',
        API_NAME: 'magenta'
    }

app_constants = AppConstants()
