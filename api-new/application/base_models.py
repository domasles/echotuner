"""Base models and common data structures."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Song(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    spotify_id: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    genres: Optional[List[str]] = []


class UserContext(BaseModel):
    context: dict = {}


class RateLimitStatus(BaseModel):
    user_id: str  # Format: spotify_{id} or google_{id}
    requests_made_today: int
    max_requests_per_day: int
    can_make_request: bool
    reset_time: Optional[str] = None
    playlist_limit_enabled: bool = False
