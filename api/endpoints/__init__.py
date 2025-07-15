# A file used to make endpoints a Python package

from .auth import (
    auth_init, auth_callback, validate_session, check_session, 
    get_authenticated_rate_limit_status, register_device, logout,
    cleanup_sessions, get_account_type, get_auth_mode
)

from .playlists import (
    generate_playlist, update_playlist_draft, 
    get_library_playlists, get_draft_playlist, delete_draft_playlist
)

from .spotify import (
    create_spotify_playlist, get_spotify_playlist_tracks, 
    delete_spotify_playlist, remove_track_from_spotify_playlist
)

from .personality import (
    save_user_personality, load_user_personality, clear_user_personality,
    get_followed_artists, search_artists
)

from .ai import (
    get_ai_models, test_ai_model, production_readiness_check
)

from .config import (
    health_check, get_config, reload_config, root
)

from .server import (
    get_server_mode
)
