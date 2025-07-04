"""Core application models and data structures for EchoTuner."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DeviceRegistrationRequest(BaseModel):
    platform: str
    app_version: Optional[str] = None
    device_fingerprint: Optional[str] = None

class DeviceRegistrationResponse(BaseModel):
    device_id: str
    registration_timestamp: int

class Song(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    spotify_id: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    genres: Optional[List[str]] = []

class UserContext(BaseModel):
    age_range: Optional[str] = None
    favorite_genres: Optional[List[str]] = []
    favorite_artists: Optional[List[str]] = []
    disliked_artists: Optional[List[str]] = []
    recent_listening_history: Optional[List[str]] = []
    music_discovery_preference: Optional[str] = None
    energy_preference: Optional[str] = None
    include_spotify_artists: Optional[bool] = True
    happy_music_preference: Optional[str] = None
    sad_music_preference: Optional[str] = None
    workout_music_preference: Optional[str] = None
    focus_music_preference: Optional[str] = None
    relaxation_music_preference: Optional[str] = None
    party_music_preference: Optional[str] = None
    discovery_openness: Optional[str] = None
    explicit_content_preference: Optional[str] = None
    instrumental_preference: Optional[str] = None
    decade_preference: Optional[List[str]] = []
    music_activity_preference: Optional[str] = None
    vocal_preference: Optional[str] = None
    genre_openness: Optional[str] = None

class SpotifyArtist(BaseModel):
    id: str
    name: str
    image_url: Optional[str] = None
    genres: Optional[List[str]] = []
    popularity: Optional[int] = None

class PlaylistRequest(BaseModel):
    prompt: str
    device_id: str
    session_id: str
    user_context: Optional[UserContext] = None
    current_songs: Optional[List[Song]] = None
    count: Optional[int] = 30
    playlist_id: Optional[str] = None
    discovery_strategy: Optional[str] = "balanced"

class PlaylistResponse(BaseModel):
    songs: List[Song]
    generated_from: str
    total_count: int
    is_refinement: Optional[bool] = False
    playlist_id: Optional[str] = None

class RateLimitStatus(BaseModel):
    device_id: str
    requests_made_today: int
    max_requests_per_day: int
    refinements_used: int
    max_refinements: int
    can_make_request: bool
    can_refine: bool
    reset_time: Optional[str] = None
    playlist_limit_enabled: bool = False
    refinement_limit_enabled: bool = False

class AuthInitRequest(BaseModel):
    device_id: str
    platform: str

class AuthInitResponse(BaseModel):
    auth_url: str
    state: str
    device_id: str

class AuthCallbackRequest(BaseModel):
    code: str
    state: str

class AuthCallbackResponse(BaseModel):
    session_id: str
    redirect_url: str

class SessionValidationRequest(BaseModel):
    session_id: str
    device_id: str

class SessionValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    spotify_user_id: Optional[str] = None

class PlaylistDraft(BaseModel):
    id: str
    device_id: str
    session_id: Optional[str] = None
    prompt: str
    songs: List[Song]
    created_at: datetime
    updated_at: datetime
    refinements_used: int = 0
    status: str = "draft" # draft, added_to_spotify
    spotify_playlist_id: Optional[str] = None

class SpotifyPlaylistRequest(BaseModel):
    playlist_id: str
    device_id: str
    session_id: str
    name: str
    description: Optional[str] = None
    public: Optional[bool] = False
    songs: Optional[List[Song]] = None  # For demo accounts to provide current song list

class SpotifyPlaylistResponse(BaseModel):
    success: bool
    spotify_playlist_id: str
    playlist_url: str
    message: str

class SpotifyPlaylistInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tracks_count: int
    refinements_used: int = 0
    max_refinements: int = 3
    can_refine: bool = True
    spotify_url: Optional[str] = None
    images: Optional[List[dict]] = []

class LibraryPlaylistsRequest(BaseModel):
    device_id: str
    session_id: str
    include_drafts: Optional[bool] = True

class LibraryPlaylistsResponse(BaseModel):
    drafts: List[PlaylistDraft]
    spotify_playlists: List[SpotifyPlaylistInfo]

class UserPersonalityRequest(BaseModel):
    session_id: str
    device_id: str
    user_context: UserContext

class UserPersonalityClearRequest(BaseModel):
    session_id: str
    device_id: str

class UserPersonalityResponse(BaseModel):
    success: bool
    message: str

class FollowedArtistsRequest(BaseModel):
    session_id: str
    device_id: str

class FollowedArtistsResponse(BaseModel):
    artists: List[SpotifyArtist]

class ArtistSearchRequest(BaseModel):
    session_id: str
    device_id: str
    query: str
    limit: Optional[int] = 20

class ArtistSearchResponse(BaseModel):
    artists: List[SpotifyArtist]

class DemoPlaylistRefinementsRequest(BaseModel):
    playlist_id: str
    device_id: str
    session_id: str
