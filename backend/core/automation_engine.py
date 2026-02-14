"""
Safe Automation Engine - Replaces exec() with Command Validation

This is the CRITICAL SECURITY component that eliminates arbitrary code execution.
Only whitelisted commands from backend/models/commands.py can be executed.
"""
import asyncio
import datetime
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from backend.models.commands import (
    Command,
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
    SecurityError,
    ALLOWED_COMMAND_TYPES
)


class ExecutionResult:
    """Result of an automation execution"""

    def __init__(self):
        self.success: bool = False
        self.commands_executed: int = 0
        self.execution_time_ms: int = 0
        self.screenshots: List[str] = []  # File paths
        self.screenshot_data: List[Dict[str, str]] = []  # Base64 data for display
        self.extracted_data: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.error_command_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "commands_executed": self.commands_executed,
            "execution_time_ms": self.execution_time_ms,
            "screenshots": self.screenshots,
            "screenshot_data": self.screenshot_data,
            "extracted_data": self.extracted_data,
            "error": self.error,
            "error_command_index": self.error_command_index
        }


class AutomationEngine:
    """
    Safe automation engine that executes only whitelisted commands.

    NO ARBITRARY CODE EXECUTION - all commands are validated and dispatched
    to pre-written, tested handlers.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Ensure logs directory exists
        os.makedirs("logs/screenshots", exist_ok=True)

    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()

        # Launch Chrome in headless mode (required for Docker environment)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )

        self.context = await self.browser.new_context(
            ignore_https_errors=True,  # Handle SSL warnings
            viewport={"width": 1920, "height": 1080}
        )

        self.page = await self.context.new_page()

    async def execute_commands(
        self,
        commands: List[Command]
    ) -> ExecutionResult:
        """
        Execute a list of validated commands safely.

        Args:
            commands: List of Command objects (already validated by Pydantic)

        Returns:
            ExecutionResult with success/failure status
        """
        result = ExecutionResult()
        start_time = datetime.datetime.now()

        try:
            # Initialize browser
            await self.initialize()

            # Execute each command
            for i, cmd in enumerate(commands):
                try:
                    await self._execute_single_command(cmd, result)
                    result.commands_executed += 1
                except Exception as e:
                    result.error = str(e)
                    result.error_command_index = i
                    raise

            # Mark as successful
            result.success = True

        except Exception as e:
            result.success = False
            result.error = result.error or str(e)

        finally:
            # Calculate execution time
            end_time = datetime.datetime.now()
            result.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Cleanup
            await self.cleanup()

        return result

    async def _execute_single_command(
        self,
        cmd: Command,
        result: ExecutionResult
    ):
        """
        Execute a single command by dispatching to the appropriate handler.

        Security: Only commands with types in ALLOWED_COMMAND_TYPES are accepted.
        """
        cmd_type = cmd.type

        # Verify command type is in whitelist (should already be validated)
        if cmd_type not in ALLOWED_COMMAND_TYPES:
            raise SecurityError(f"Command type '{cmd_type}' not in whitelist")

        # Dispatch to handler
        if isinstance(cmd, NavigateCommand):
            await self._handle_navigate(cmd)
        elif isinstance(cmd, ClickCommand):
            await self._handle_click(cmd)
        elif isinstance(cmd, FillCommand):
            await self._handle_fill(cmd)
        elif isinstance(cmd, WaitForCommand):
            await self._handle_wait_for(cmd)
        elif isinstance(cmd, WaitForNavigationCommand):
            await self._handle_wait_for_navigation(cmd)
        elif isinstance(cmd, ScreenshotCommand):
            await self._handle_screenshot(cmd, result)
        elif isinstance(cmd, ExtractTextCommand):
            await self._handle_extract_text(cmd, result)
        elif isinstance(cmd, HandleDialogCommand):
            await self._handle_dialog(cmd)
        elif isinstance(cmd, SelectOptionCommand):
            await self._handle_select_option(cmd)
        elif isinstance(cmd, PressKeyCommand):
            await self._handle_press_key(cmd)
        else:
            raise SecurityError(f"Unknown command type: {cmd_type}")

    # Command Handlers - Pre-written, tested, safe implementations

    async def _handle_navigate(self, cmd: NavigateCommand):
        """Navigate to a URL"""
        await self.page.goto(str(cmd.url), wait_until="load")

    async def _handle_click(self, cmd: ClickCommand):
        """Click an element"""
        await self.page.click(cmd.selector, timeout=cmd.timeout)

    async def _handle_fill(self, cmd: FillCommand):
        """Fill an input field"""
        await self.page.fill(cmd.selector, cmd.value)

    async def _handle_wait_for(self, cmd: WaitForCommand):
        """Wait for an element to appear"""
        await self.page.wait_for_selector(cmd.selector, timeout=cmd.timeout)

    async def _handle_wait_for_navigation(self, cmd: WaitForNavigationCommand):
        """Wait for navigation to complete"""
        await self.page.wait_for_load_state("networkidle", timeout=cmd.timeout)

    async def _handle_screenshot(self, cmd: ScreenshotCommand, result: ExecutionResult):
        """Take a screenshot and encode for display"""
        import base64

        # Generate filename if not provided
        if cmd.filename:
            filename = cmd.filename
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        filepath = os.path.join("logs/screenshots", filename)
        await self.page.screenshot(path=filepath, full_page=True)
        result.screenshots.append(filepath)

        # Also encode as base64 for inline display
        try:
            with open(filepath, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                result.screenshot_data.append({
                    "filename": filename,
                    "data": image_data,
                    "path": filepath
                })
        except Exception as e:
            print(f"Warning: Could not encode screenshot for display: {e}")

    async def _handle_extract_text(
        self,
        cmd: ExtractTextCommand,
        result: ExecutionResult
    ):
        """Extract text from an element"""
        text = await self.page.text_content(cmd.selector)
        result.extracted_data[cmd.selector] = text

    async def _handle_dialog(self, cmd: HandleDialogCommand):
        """Handle browser dialogs"""
        # Set up dialog handler
        async def dialog_handler(dialog):
            if cmd.action == "accept":
                await dialog.accept(cmd.prompt_text or "")
            else:
                await dialog.dismiss()

        self.page.on("dialog", dialog_handler)

    async def _handle_select_option(self, cmd: SelectOptionCommand):
        """Select an option from a dropdown"""
        await self.page.select_option(cmd.selector, value=cmd.value)

    async def _handle_press_key(self, cmd: PressKeyCommand):
        """Press a keyboard key"""
        await self.page.keyboard.press(cmd.key)

    async def cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# Convenience function for one-off executions
async def execute_automation(
    commands: List[Command],
    headless: bool = False
) -> ExecutionResult:
    """
    Execute automation commands with a fresh engine instance.

    Args:
        commands: List of validated Command objects
        headless: Run browser in headless mode

    Returns:
        ExecutionResult
    """
    engine = AutomationEngine(headless=headless)
    return await engine.execute_commands(commands)
