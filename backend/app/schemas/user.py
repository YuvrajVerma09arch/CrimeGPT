from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    badge_no: str
    role: str
    station: str | None = None
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    name: str
    badge_no: str
    role: str = Field(pattern="^(IO|SHO|LEGAL_ADVISOR)$")
    station: str | None = None
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    badge_no: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
