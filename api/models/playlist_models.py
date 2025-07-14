"""Playlist and draft management models."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .base_models import Song, UserContext
from .spotify_models import SpotifyPlaylistInfo


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


class PlaylistDraft(BaseModel):
    id: str
    device_id: str
    session_id: Optional[str] = None
    prompt: str
    songs: List[Song]
    created_at: datetime
    updated_at: datetime
    refinements_used: int = 0
    status: str = "draft"  # draft, added_to_spotify
    spotify_playlist_id: Optional[str] = None
    spotify_playlist_url: Optional[str] = None


class PlaylistDraftRequest(BaseModel):
    playlist_id: str
    device_id: str


class LibraryPlaylistsRequest(BaseModel):
    device_id: str
    session_id: str
    include_drafts: Optional[bool] = True


# Forward reference to avoid circular import
class LibraryPlaylistsResponse(BaseModel):
    drafts: List[PlaylistDraft]
    spotify_playlists: List["SpotifyPlaylistInfo"]
