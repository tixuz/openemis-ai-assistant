"""
User Variables Models

Allows users to store reusable values like credentials, selectors, URLs.
"""
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class UserVariable(BaseModel):
    """A single user variable (key-value pair)"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str = Field(
        description="Variable key (e.g., 'username', 'school_code')",
        min_length=1,
        max_length=100
    )
    value: str = Field(
        description="Variable value",
        max_length=1000
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description"
    )
    type: Literal["text", "password", "url", "selector", "number"] = Field(
        default="text",
        description="Variable type for UI rendering"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "key": "username",
                "value": "admin",
                "description": "OpenEMIS login username",
                "type": "text",
                "created_at": "2026-02-14T01:00:00Z",
                "updated_at": "2026-02-14T01:00:00Z"
            }
        }


class VariableCreate(BaseModel):
    """Request to create/update a variable"""
    key: str = Field(min_length=1, max_length=100)
    value: str = Field(max_length=1000)
    description: Optional[str] = None
    type: Literal["text", "password", "url", "selector", "number"] = "text"


class VariableResponse(BaseModel):
    """Response with variable (password values masked)"""
    id: str
    key: str
    value: str  # Masked if type=password
    description: Optional[str]
    type: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_variable(var: UserVariable, mask_password: bool = True) -> "VariableResponse":
        """Convert UserVariable to response, optionally masking passwords"""
        value = var.value
        if mask_password and var.type == "password" and value:
            # Mask password: show first 2 and last 2 chars
            if len(value) > 4:
                value = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                value = "*" * len(value)

        return VariableResponse(
            id=var.id,
            key=var.key,
            value=value,
            description=var.description,
            type=var.type,
            created_at=var.created_at,
            updated_at=var.updated_at
        )


class VariablesListResponse(BaseModel):
    """List of user variables"""
    variables: list[VariableResponse]
    total: int
