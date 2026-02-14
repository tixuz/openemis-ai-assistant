"""
Safe Command Models - Replaces Dangerous exec() with Validated Commands

This module defines the WHITELIST of allowed automation commands.
Only these command types can be executed - no arbitrary code execution.
"""
from pydantic import BaseModel, HttpUrl, field_validator, Field
from typing import Literal, Union, Optional, List
import re


class SecurityError(Exception):
    """Raised when a command violates security policies"""
    pass


class NavigateCommand(BaseModel):
    """Navigate to a URL - only allowed domains"""
    type: Literal["navigate"]
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_domain(cls, v):
        """Only allow localhost (any port) and openemis.org domains"""
        url_str = str(v)
        allowed_domains = [
            "localhost",      # Matches localhost:any_port
            "127.0.0.1",      # Matches 127.0.0.1:any_port
            "0.0.0.0",
            "openemis.org",
            "demo.openemis.org"
        ]

        if not any(domain in url_str for domain in allowed_domains):
            raise ValueError(
                f"Domain not in whitelist. Allowed: {', '.join(allowed_domains)} (any port)"
            )
        return v


class ClickCommand(BaseModel):
    """Click an element by CSS selector"""
    type: Literal["click"]
    selector: str
    timeout: int = Field(default=5000, ge=100, le=30000)

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v):
        """Basic validation to prevent selector injection"""
        if len(v) > 500:
            raise ValueError("Selector too long")

        # Block suspicious patterns
        dangerous = ["javascript:", "data:", "vbscript:", "<script"]
        if any(pattern in v.lower() for pattern in dangerous):
            raise SecurityError(f"Selector contains dangerous pattern")

        return v


class FillCommand(BaseModel):
    """Fill an input field with text"""
    type: Literal["fill"]
    selector: str
    value: str

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v):
        """Basic validation to prevent selector injection"""
        if len(v) > 500:
            raise ValueError("Selector too long")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v):
        """Prevent injection of huge strings"""
        if len(v) > 10000:
            raise ValueError("Value too long (max 10000 characters)")
        return v


class WaitForCommand(BaseModel):
    """Wait for an element to appear"""
    type: Literal["wait_for"]
    selector: str
    timeout: int = Field(default=5000, ge=100, le=30000)

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v):
        if len(v) > 500:
            raise ValueError("Selector too long")
        return v


class WaitForNavigationCommand(BaseModel):
    """Wait for page navigation to complete"""
    type: Literal["wait_for_navigation"]
    timeout: int = Field(default=5000, ge=100, le=30000)


class ScreenshotCommand(BaseModel):
    """Take a screenshot of the current page"""
    type: Literal["screenshot"]
    filename: Optional[str] = None

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        """Prevent path traversal attacks"""
        if v is None:
            return v

        # Only allow safe filenames
        if not re.match(r'^[a-zA-Z0-9_\-]+\.(png|jpg|jpeg)$', v):
            raise SecurityError(
                "Filename must match pattern: [a-zA-Z0-9_-]+.(png|jpg|jpeg)"
            )

        # Block path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise SecurityError("Path traversal not allowed in filename")

        return v


class ExtractTextCommand(BaseModel):
    """Extract text content from an element"""
    type: Literal["extract_text"]
    selector: str

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v):
        if len(v) > 500:
            raise ValueError("Selector too long")
        return v


class HandleDialogCommand(BaseModel):
    """Accept or dismiss browser dialogs (alert, confirm, prompt)"""
    type: Literal["handle_dialog"]
    action: Literal["accept", "dismiss"]
    prompt_text: Optional[str] = None


class SelectOptionCommand(BaseModel):
    """Select an option from a dropdown"""
    type: Literal["select_option"]
    selector: str
    value: str

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v):
        if len(v) > 500:
            raise ValueError("Selector too long")
        return v


class PressKeyCommand(BaseModel):
    """Press a keyboard key"""
    type: Literal["press_key"]
    key: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Only allow known keyboard keys"""
        allowed_keys = [
            "Enter", "Tab", "Escape", "Backspace", "Delete",
            "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
            "Home", "End", "PageUp", "PageDown"
        ]

        if v not in allowed_keys:
            raise ValueError(f"Key '{v}' not in allowed list: {allowed_keys}")

        return v


# Union of all allowed command types
Command = Union[
    NavigateCommand,
    ClickCommand,
    FillCommand,
    WaitForCommand,
    WaitForNavigationCommand,
    ScreenshotCommand,
    ExtractTextCommand,
    HandleDialogCommand,
    SelectOptionCommand,
    PressKeyCommand,
]


# Export the command types for validation
ALLOWED_COMMAND_TYPES = {
    "navigate",
    "click",
    "fill",
    "wait_for",
    "wait_for_navigation",
    "screenshot",
    "extract_text",
    "handle_dialog",
    "select_option",
    "press_key"
}


class CommandList(BaseModel):
    """Container for a list of commands"""
    commands: List[Command]

    @field_validator("commands")
    @classmethod
    def validate_command_list(cls, v):
        """Ensure reasonable command count"""
        if len(v) > 50:
            raise ValueError("Too many commands (max 50 per execution)")

        if len(v) == 0:
            raise ValueError("At least one command required")

        return v
