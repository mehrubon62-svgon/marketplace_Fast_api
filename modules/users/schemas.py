from pydantic import BaseModel, EmailStr
from models import RoleEnum


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileOut(BaseModel):
    avatar_url: str | None = None
    phone: str | None = None
    bio: str | None = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    avatar_url: str | None = None
    phone: str | None = None
    bio: str | None = None
