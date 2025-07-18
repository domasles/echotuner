"""User personality and preferences models."""

from .base_models import UserContext
from pydantic import BaseModel
from typing import Optional

class UserPersonalityRequest(BaseModel):
    session_id: str
    device_id: str
    user_context: Optional[UserContext]

class UserPersonalityClearRequest(BaseModel):
    session_id: str
    device_id: str

class UserPersonalityResponse(BaseModel):
    success: bool
    message: str
