"""
Test Command Models - Verify security validation
"""
import pytest
from pydantic import ValidationError

from backend.models.commands import (
    NavigateCommand,
    ClickCommand,
    FillCommand,
    SecurityError,
    CommandList
)


class TestNavigateCommand:
    """Test NavigateCommand validation"""

    def test_valid_localhost_url(self):
        """Should accept localhost URLs"""
        cmd = NavigateCommand(type="navigate", url="http://localhost:8482/core")
        assert cmd.url is not None

    def test_valid_openemis_url(self):
        """Should accept openemis.org URLs"""
        cmd = NavigateCommand(type="navigate", url="https://demo.openemis.org/core")
        assert cmd.url is not None

    def test_invalid_domain_rejected(self):
        """Should reject URLs outside whitelist"""
        with pytest.raises(ValidationError) as exc_info:
            NavigateCommand(type="navigate", url="https://malicious.com/steal")
        assert "not in whitelist" in str(exc_info.value)

    def test_javascript_protocol_rejected(self):
        """Should reject javascript: protocol"""
        with pytest.raises(ValidationError):
            NavigateCommand(type="navigate", url="javascript:alert('xss')")


class TestClickCommand:
    """Test ClickCommand validation"""

    def test_valid_selector(self):
        """Should accept valid CSS selector"""
        cmd = ClickCommand(type="click", selector="#login-button")
        assert cmd.selector == "#login-button"

    def test_timeout_within_limits(self):
        """Should accept timeout within limits"""
        cmd = ClickCommand(type="click", selector="#btn", timeout=10000)
        assert cmd.timeout == 10000

    def test_timeout_too_long_rejected(self):
        """Should reject timeout over 30 seconds"""
        with pytest.raises(ValidationError):
            ClickCommand(type="click", selector="#btn", timeout=60000)

    def test_dangerous_selector_rejected(self):
        """Should reject selectors with dangerous patterns"""
        with pytest.raises((ValidationError, SecurityError)):
            ClickCommand(type="click", selector="<script>alert('xss')</script>")


class TestFillCommand:
    """Test FillCommand validation"""

    def test_valid_fill(self):
        """Should accept valid fill command"""
        cmd = FillCommand(
            type="fill",
            selector="#username",
            value="admin"
        )
        assert cmd.value == "admin"

    def test_value_too_long_rejected(self):
        """Should reject values over 10,000 characters"""
        long_value = "A" * 10001
        with pytest.raises(ValidationError) as exc_info:
            FillCommand(type="fill", selector="#input", value=long_value)
        assert "too long" in str(exc_info.value).lower()


class TestCommandList:
    """Test CommandList validation"""

    def test_valid_command_list(self):
        """Should accept valid command list"""
        commands = [
            {"type": "navigate", "url": "https://demo.openemis.org"},
            {"type": "click", "selector": "#button"}
        ]
        cmd_list = CommandList(commands=commands)
        assert len(cmd_list.commands) == 2

    def test_empty_list_rejected(self):
        """Should reject empty command list"""
        with pytest.raises(ValidationError) as exc_info:
            CommandList(commands=[])
        assert "at least one command" in str(exc_info.value).lower()

    def test_too_many_commands_rejected(self):
        """Should reject over 50 commands"""
        commands = [{"type": "screenshot"}] * 51
        with pytest.raises(ValidationError) as exc_info:
            CommandList(commands=commands)
        assert "too many" in str(exc_info.value).lower()
