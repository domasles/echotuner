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
