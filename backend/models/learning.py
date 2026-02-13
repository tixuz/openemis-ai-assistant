"""
Learning Example Models

Stores successful automation examples for few-shot learning.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class LearningExample(BaseModel):
    """A successful automation execution to learn from"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_description: str = Field(..., description="What the user asked for")
    user_intent: str = Field(..., description="Original user message")
    commands: List[Dict[str, Any]] = Field(..., description="Commands that were executed")
    success: bool = Field(default=True)
    context: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the task")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_time_ms: int = Field(default=0)
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_description": "Login to OpenEMIS admin panel",
                "user_intent": "login as admin",
                "commands": [
                    {"type": "navigate", "url": "https://demo.openemis.org/core"},
                    {"type": "fill", "selector": "#username", "value": "admin"},
                    {"type": "fill", "selector": "#password", "value": "demo"},
                    {"type": "click", "selector": "button[type='submit']"},
                    {"type": "wait_for_navigation", "timeout": 5000}
                ],
                "success": True,
                "context": {"domain": "demo.openemis.org", "page_type": "login"},
                "timestamp": "2026-02-14T00:04:29Z",
                "execution_time_ms": 3450,
                "tags": ["authentication", "openemis", "admin"]
            }
        }
