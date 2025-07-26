"""User personality and preferences models."""

from .base_models import UserContext
from pydantic import BaseModel
from typing import Optional

class UserPersonalityResponse(BaseModel):
    success: bool
    message: str
