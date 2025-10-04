from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    ATTORNEY = "attorney"
    CLIENT = "client"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = Field(..., description="User role: attorney or client")


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
