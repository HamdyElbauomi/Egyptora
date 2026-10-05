"""Request/response shapes for accounts. Owner: Person 1."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    language: str = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    language: str


class UpdateMeIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    language: str | None = None
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8)
