"""User models and Role-Based Access Control (RBAC) schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

EmailStr = str


class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.AGENT
    tenant_id: str = "default-tenant"
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: str
    created_at: Optional[str] = None


class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: str


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
