"""
Reusable Automation Scripts - Admin Script Library

Allows admins to save and reuse automation scripts with parameters.
Unlike learning examples (passive), these are active, reusable components.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ScriptParameter(BaseModel):
    """Input parameter for a script"""
    name: str = Field(..., description="Parameter name (e.g., 'username', 'institution_code')")
    type: str = Field("text", description="Parameter type: text, password, url, selector, number, script")
    description: Optional[str] = Field(None, description="Help text for this parameter")
    default_value: Optional[str] = Field(None, description="Default value")
    required: bool = Field(True, description="Is this parameter required?")


class AutomationScript(BaseModel):
    """Reusable automation script with parameters"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Script name (unique identifier)")
    description: str = Field(..., description="What this script does")
    commands: List[Dict[str, Any]] = Field(..., description="Playwright commands")
    parameters: List[ScriptParameter] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    created_by: str = Field(..., description="Username of creator")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_count: int = Field(default=0, description="How many times this script has been run")

    @validator("name")
    @classmethod
    def validate_name(cls, v):
        """Script names must be alphanumeric + underscores/hyphens"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Script name must be alphanumeric (underscores/hyphens allowed)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "openemis_login",
                "description": "Login to OpenEMIS with credentials",
                "commands": [
                    {"type": "navigate", "url": "{site_url}"},
                    {"type": "fill", "selector": "#username", "value": "{username}"},
                    {"type": "fill", "selector": "#password", "value": "{password}"},
                    {"type": "click", "selector": "button[type='submit']"},
                    {"type": "wait_for_navigation", "timeout": 5000}
                ],
                "parameters": [
                    {
                        "name": "site_url",
                        "type": "url",
                        "description": "OpenEMIS site URL",
                        "default_value": "https://host.docker.internal:8482/core",
                        "required": True
                    },
                    {
                        "name": "username",
                        "type": "text",
                        "description": "Login username",
                        "required": True
                    },
                    {
                        "name": "password",
                        "type": "password",
                        "description": "Login password",
                        "required": True
                    }
                ],
                "tags": ["authentication", "openemis", "login"],
                "created_by": "admin",
                "created_at": "2026-02-14T10:00:00Z",
                "execution_count": 42
            }
        }


class ScriptExecutionRequest(BaseModel):
    """Request to execute a saved script"""
    script_name: str = Field(..., description="Name of script to execute")
    parameters: Dict[str, str] = Field(default_factory=dict, description="Parameter values")
    take_screenshot: bool = Field(True, description="Take screenshot after execution")
    continue_session: bool = Field(False, description="Keep browser context alive for next execution")


class ScriptChainRequest(BaseModel):
    """Execute multiple scripts in sequence"""
    scripts: List[ScriptExecutionRequest] = Field(..., description="Scripts to execute in order")
    session_name: Optional[str] = Field(None, description="Named session to reuse browser context")

    @validator("scripts")
    @classmethod
    def validate_scripts(cls, v):
        if len(v) < 1:
            raise ValueError("At least one script required")
        if len(v) > 10:
            raise ValueError("Maximum 10 scripts per chain")
        return v
