"""User personality and preferences models."""

from pydantic import BaseModel


class UserPersonalityResponse(BaseModel):
    success: bool
    message: str
