"""Authentication and device management models."""

from pydantic import BaseModel
from typing import Optional


class DeviceRegistrationRequest(BaseModel):
    platform: str
    app_version: Optional[str] = None
    device_fingerprint: Optional[str] = None


class DeviceRegistrationResponse(BaseModel):
    device_id: str
    registration_timestamp: int


class AuthInitRequest(BaseModel):
    device_id: str
    platform: str


class AuthInitResponse(BaseModel):
    auth_url: str
    state: str
    device_id: str


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


class AccountTypeResponse(BaseModel):
    account_type: str
