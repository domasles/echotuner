"""Core application models and data structures for EchoTuner."""

from pydantic import BaseModel
from typing import List, Optional

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
    recent_listening_history: Optional[List[str]] = []
    music_discovery_preference: Optional[str] = "balanced"
    energy_preference: Optional[str] = "medium"

class PlaylistRequest(BaseModel):
    prompt: str
    device_id: str
    session_id: str
    user_context: Optional[UserContext] = None
    current_songs: Optional[List[Song]] = None
    count: Optional[int] = 30

class PlaylistResponse(BaseModel):
    songs: List[Song]
    generated_from: str
    total_count: int
    is_refinement: Optional[bool] = False

class RateLimitStatus(BaseModel):
    device_id: str
    requests_made_today: int
    max_requests_per_day: int
    refinements_used: int
    max_refinements: int
    can_make_request: bool
    can_refine: bool
    reset_time: Optional[str] = None

class AuthInitRequest(BaseModel):
    device_id: str
    platform: str

class AuthInitResponse(BaseModel):
    auth_url: str
    state: str

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
