"""Spotify integration models."""

from pydantic import BaseModel
from typing import List, Optional
from .base_models import Song


class SpotifyArtist(BaseModel):
    id: str
    name: str
    image_url: Optional[str] = None
    genres: Optional[List[str]] = []
    popularity: Optional[int] = None


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


class SpotifyPlaylistTracksRequest(BaseModel):
    playlist_id: str
    session_id: str
    device_id: str


class SpotifyPlaylistDeleteRequest(BaseModel):
    playlist_id: str
    session_id: str
    device_id: str


class SpotifyPlaylistTrackRemoveRequest(BaseModel):
    playlist_id: str
    track_uri: str
    session_id: str
    device_id: str


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
