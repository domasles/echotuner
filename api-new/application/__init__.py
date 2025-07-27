"""
Centralized model imports.
Maintains backward compatibility while organizing models into logical groups.
"""

# Base models
from .base_models import Song, UserContext, RateLimitStatus

# Playlist models
from .playlist_models import (
    PlaylistRequest, PlaylistResponse, PlaylistDraft,
    LibraryPlaylistsRequest, LibraryPlaylistsResponse
)

# Spotify models
from .spotify_models import (
    SpotifyArtist, SpotifyPlaylistRequest, SpotifyPlaylistResponse,
    SpotifyPlaylistInfo,
    SpotifyPlaylistTrackRemoveRequest,
    FollowedArtistsRequest, FollowedArtistsResponse,
    ArtistSearchRequest, ArtistSearchResponse
)

# User models
from .user_models import (
    UserPersonalityResponse
)
