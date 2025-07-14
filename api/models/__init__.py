"""
Centralized model imports.
Maintains backward compatibility while organizing models into logical groups.
"""

# Base models
from .base_models import Song, UserContext, RateLimitStatus

# Authentication models  
from .auth_models import (
    DeviceRegistrationRequest, DeviceRegistrationResponse,
    AuthInitRequest, AuthInitResponse,
    AuthCallbackRequest, AuthCallbackResponse,
    SessionValidationRequest, SessionValidationResponse,
    DemoPlaylistRefinementsRequest
)

# Playlist models
from .playlist_models import (
    PlaylistRequest, PlaylistResponse, PlaylistDraft,
    PlaylistDraftRequest, LibraryPlaylistsRequest, LibraryPlaylistsResponse
)

# Spotify models
from .spotify_models import (
    SpotifyArtist, SpotifyPlaylistRequest, SpotifyPlaylistResponse,
    SpotifyPlaylistInfo, SpotifyPlaylistTracksRequest,
    SpotifyPlaylistDeleteRequest, SpotifyPlaylistTrackRemoveRequest,
    FollowedArtistsRequest, FollowedArtistsResponse,
    ArtistSearchRequest, ArtistSearchResponse
)

# User models
from .user_models import (
    UserPersonalityRequest, UserPersonalityClearRequest,
    UserPersonalityResponse
)
