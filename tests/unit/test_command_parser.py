"""
Test Command Parser
"""
import pytest
import json

from backend.core.command_parser import CommandParser, ParseError


class TestCommandParser:
    """Test CommandParser functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.parser = CommandParser()

    def test_parse_plain_json(self):
        """Should parse plain JSON"""
        json_str = json.dumps({
            "commands": [
                {"type": "navigate", "url": "https://demo.openemis.org"}
            ]
        })
        commands = self.parser.parse(json_str)
        assert len(commands) == 1
        assert commands[0].type == "navigate"

    def test_parse_markdown_code_block(self):
        """Should extract JSON from markdown code block"""
        json_str = '''```json
{
  "commands": [
    {"type": "navigate", "url": "https://demo.openemis.org"}
  ]
}
```'''
        commands = self.parser.parse(json_str)
        assert len(commands) == 1

    def test_parse_code_block_without_json_marker(self):
        """Should extract JSON from generic code block"""
        json_str = '''```
{
  "commands": [
    {"type": "click", "selector": "#button"}
  ]
}
```'''
        commands = self.parser.parse(json_str)
        assert len(commands) == 1
        assert commands[0].type == "click"

    def test_invalid_json_raises_error(self):
        """Should raise ParseError for invalid JSON"""
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse("not valid json {")
        assert "Invalid JSON" in str(exc_info.value)

    def test_missing_commands_key_raises_error(self):
        """Should raise ParseError if commands key missing"""
        json_str = json.dumps({"data": []})
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(json_str)
        assert "missing 'commands'" in str(exc_info.value).lower()

    def test_validate_single_command(self):
        """Should validate single command"""
        cmd_dict = {"type": "screenshot", "filename": "test.png"}
        command = self.parser.validate_command(cmd_dict)
        assert command.type == "screenshot"

    def test_invalid_command_type_raises_error(self):
        """Should raise error for invalid command type"""
        cmd_dict = {"type": "malicious_eval", "code": "evil"}
        with pytest.raises(Exception):  # SecurityError or ValidationError
            self.parser.validate_command(cmd_dict)
