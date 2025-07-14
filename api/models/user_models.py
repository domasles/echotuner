"""User personality and preferences models."""

from pydantic import BaseModel
from .base_models import UserContext


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
