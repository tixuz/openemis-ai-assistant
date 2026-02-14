"""
Chat History Models

Stores conversation history between users and the AI assistant.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    """A single chat message with AI response and optional automation result"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(description="User's unique identifier")
    username: str = Field(description="User's display name")

    # User's message
    message: str = Field(description="User's input message")

    # AI's response
    response: str = Field(description="AI assistant's response")

    # Automation details (if any)
    commands_generated: Optional[int] = Field(
        default=None,
        description="Number of commands generated"
    )
    executed: bool = Field(
        default=False,
        description="Whether automation was executed"
    )
    execution_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full execution result including screenshots, timing, etc."
    )

    # Metadata
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When this message was sent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "username": "teacher1",
                "message": "Login to OpenEMIS as admin",
                "response": "✅ Automation completed successfully!\n\nExecuted 5 commands in 9549ms.",
                "commands_generated": 5,
                "executed": True,
                "execution_result": {
                    "success": True,
                    "commands_executed": 5,
                    "execution_time_ms": 9549,
                    "screenshots": [],
                    "extracted_data": {}
                },
                "timestamp": "2026-02-14T00:49:24.251404"
            }
        }
