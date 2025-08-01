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
    name: str
    description: Optional[str] = None
    public: Optional[bool] = False
    songs: Optional[List[Song]] = None  # For shared mode to provide current song list


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
    spotify_url: Optional[str] = None


class SpotifyPlaylistTrackRemoveRequest(BaseModel):
    track_uri: str


class FollowedArtistsRequest(BaseModel):
    user_id: str  # Format: spotify_{id} or google_{id}


class FollowedArtistsResponse(BaseModel):
    artists: List[SpotifyArtist]


class ArtistSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20


class ArtistSearchResponse(BaseModel):
    artists: List[SpotifyArtist]
