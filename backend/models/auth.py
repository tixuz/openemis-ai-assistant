"""
Authentication Models

User, token, and authentication-related data models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional
from datetime import datetime


class User(BaseModel):
    """User account model"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Literal["admin", "user", "prompt_engineer"] = "user"
    permissions: List[str] = Field(default_factory=list)
    disabled: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Username must be alphanumeric + underscore"""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscore allowed)")
        return v.lower()


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str


class LoginRequest(BaseModel):
    """Login request payload"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    username: str
    role: str
    permissions: List[str] = Field(default_factory=list)
