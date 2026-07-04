"""
Authentication schemas.
"""

from pydantic import BaseModel, field_validator

from app.schemas.user import UserRead


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    user: UserRead
    tokens: TokenResponse