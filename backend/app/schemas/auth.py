from typing import Literal

from pydantic import BaseModel, Field


UserRole = Literal["guest", "student", "admin"]


class UserPublic(BaseModel):
    id: int | None = None
    username: str
    display_name: str
    role: UserRole
    is_guest: bool = False

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class AdminCreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)
    role: Literal["student", "admin"] = "student"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class LogoutResponse(BaseModel):
    status: str = "success"
