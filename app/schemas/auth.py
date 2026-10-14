"""Authentication and User management Pydantic schemas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import UserRole


class UserCreate(BaseModel):
    """Payload for registering a new user."""
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="User email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    role: Optional[UserRole] = Field(default=UserRole.VIEWER, description="Assigned role: ADMIN, RESEARCHER, VIEWER")


class UserLogin(BaseModel):
    """Payload for user authentication."""
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str


class UserResponse(BaseModel):
    """Public user response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """JWT bearer token structure."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
