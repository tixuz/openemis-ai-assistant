"""
Command Parser - Parse and Validate LLM JSON Output

Converts LLM's JSON response into validated Command objects.
Provides robust error handling for malformed responses.
"""
import json
import re
from typing import List, Dict, Any
from pydantic import ValidationError

from backend.models.commands import (
    Command,
    CommandList,
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
    ALLOWED_COMMAND_TYPES,
    SecurityError
)


class ParseError(Exception):
    """Raised when LLM output cannot be parsed"""
    pass


class CommandParser:
    """Parse LLM JSON output into validated Command objects"""

    def parse(self, llm_output: str) -> List[Command]:
        """
        Parse LLM output string into list of validated commands.

        Args:
            llm_output: JSON string from LLM

        Returns:
            List of validated Command objects

        Raises:
            ParseError: If output cannot be parsed
            ValidationError: If commands fail validation
        """
        # Extract JSON from markdown code blocks if present
        json_str = self._extract_json(llm_output)

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {e}")

        # Extract commands array
        if isinstance(data, dict):
            if "commands" not in data:
                raise ParseError("JSON missing 'commands' key")
            commands_data = data["commands"]
        elif isinstance(data, list):
            commands_data = data
        else:
            raise ParseError(f"Unexpected JSON type: {type(data)}")

        # Validate and convert to Command objects
        try:
            # Use CommandList for validation
            command_list = CommandList(commands=commands_data)
            return command_list.commands
        except ValidationError as e:
            raise ParseError(f"Command validation failed: {e}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM output, handling markdown code blocks.

        Supports:
        - Plain JSON
        - JSON in ```json ... ``` blocks
        - JSON in ``` ... ``` blocks
        """
        text = text.strip()

        # Try to extract from markdown code block
        patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json ... ```
            r'```\s*\n(.*?)\n```',       # ``` ... ```
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Return as-is if no code block found
        return text

    def validate_command(self, cmd_dict: Dict[str, Any]) -> Command:
        """
        Validate a single command dictionary.

        Args:
            cmd_dict: Dictionary with command data

        Returns:
            Validated Command object

        Raises:
            ValidationError: If validation fails
            SecurityError: If command type not allowed
        """
        cmd_type = cmd_dict.get("type")

        if not cmd_type:
            raise ValueError("Command missing 'type' field")

        if cmd_type not in ALLOWED_COMMAND_TYPES:
            raise SecurityError(f"Command type '{cmd_type}' not in whitelist")

        # Map command type to Pydantic model
        command_models = {
            "navigate": NavigateCommand,
            "click": ClickCommand,
            "fill": FillCommand,
            "wait_for": WaitForCommand,
            "wait_for_navigation": WaitForNavigationCommand,
            "screenshot": ScreenshotCommand,
            "extract_text": ExtractTextCommand,
            "handle_dialog": HandleDialogCommand,
            "select_option": SelectOptionCommand,
            "press_key": PressKeyCommand,
        }

        model_class = command_models.get(cmd_type)
        if not model_class:
            raise SecurityError(f"Unknown command type: {cmd_type}")

        # Validate and return
        return model_class(**cmd_dict)


# Module-level functions for convenience

def parse_llm_output(llm_output: str) -> List[Command]:
    """Parse LLM output into validated commands"""
    parser = CommandParser()
    return parser.parse(llm_output)


def is_valid_json(text: str) -> bool:
    """Check if text contains valid JSON"""
    try:
        parser = CommandParser()
        parser._extract_json(text)
        return True
    except:
        return False
