"""Playlist and draft management models."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .base_models import Song, UserContext
from .spotify_models import SpotifyPlaylistInfo


class PlaylistRequest(BaseModel):
    prompt: str
    user_context: Optional[UserContext] = None
    current_songs: Optional[List[Song]] = None
    discovery_strategy: Optional[str] = "balanced"


class PlaylistResponse(BaseModel):
    songs: List[Song]
    generated_from: str
    total_count: int
    playlist_id: Optional[str] = None


class PlaylistDraft(BaseModel):
    id: str
    user_id: str  # Format: spotify_{id} or google_{id}
    prompt: str
    songs: List[Song]
    created_at: datetime
    updated_at: datetime
    status: str = "draft"  # draft, added_to_spotify
    spotify_playlist_id: Optional[str] = None
    spotify_playlist_url: Optional[str] = None



class LibraryPlaylistsRequest(BaseModel):
    include_drafts: Optional[bool] = True


# Forward reference to avoid circular import
class LibraryPlaylistsResponse(BaseModel):
    drafts: List[PlaylistDraft]
    spotify_playlists: List["SpotifyPlaylistInfo"]
