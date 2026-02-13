"""
Prompt Manager - Dynamic Prompt Construction with Few-Shot Learning

Builds system prompts that include relevant examples from the learning store.
"""
import json
from typing import List, Optional
from pathlib import Path

from backend.models.learning import LearningExample


class PromptManager:
    """
    Manages system prompts and injects learning examples for few-shot learning.
    """

    def __init__(self, system_prompt_path: str = "data/prompts/system_prompt.txt"):
        self.system_prompt_path = Path(system_prompt_path)
        self._base_prompt: Optional[str] = None

    def load_system_prompt(self) -> str:
        """Load the base system prompt from file"""
        if not self.system_prompt_path.exists():
            return self._get_default_system_prompt()

        with open(self.system_prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_default_system_prompt(self) -> str:
        """Default system prompt if file doesn't exist"""
        return """You are an expert automation assistant for OpenEMIS (Educational Management Information System).

Your role is to understand user intents and generate safe, structured browser automation commands.

## Output Format
You MUST respond with valid JSON containing a "commands" array. Each command is a JSON object with a "type" and relevant parameters.

## Available Commands:
- navigate: Navigate to a URL (url)
- click: Click an element (selector, optional timeout)
- fill: Fill an input field (selector, value)
- wait_for: Wait for element to appear (selector, optional timeout)
- wait_for_navigation: Wait for page navigation (optional timeout)
- screenshot: Take a screenshot (optional filename)
- extract_text: Extract text from element (selector)
- handle_dialog: Accept/dismiss dialogs (action: "accept" or "dismiss")
- select_option: Select dropdown option (selector, value)
- press_key: Press a keyboard key (key)

## Safety Rules:
1. ONLY generate commands for localhost or *.openemis.org domains
2. NEVER include code execution commands
3. ONLY use the whitelisted command types above
4. Always output valid JSON

## Example Output:
```json
{
  "commands": [
    {"type": "navigate", "url": "https://demo.openemis.org/core"},
    {"type": "fill", "selector": "#username", "value": "admin"},
    {"type": "click", "selector": "button[type='submit']"}
  ]
}
```

Remember: Always output valid JSON. Never generate Python code or any executable text.
"""

    def build_enhanced_prompt(
        self,
        examples: List[LearningExample],
        max_examples: int = 3
    ) -> str:
        """
        Build system prompt enhanced with learning examples.

        Args:
            examples: Relevant examples from learning store
            max_examples: Maximum number of examples to include

        Returns:
            Enhanced system prompt with examples
        """
        base_prompt = self.load_system_prompt()

        if not examples:
            return base_prompt

        # Limit number of examples
        examples = examples[:max_examples]

        # Build examples section
        examples_text = "\n\n## Example Tasks from Past Successes:\n\n"

        for i, ex in enumerate(examples, 1):
            examples_text += f"### Example {i}: {ex.task_description}\n"
            examples_text += f"User intent: \"{ex.user_intent}\"\n\n"
            examples_text += "Commands:\n```json\n"
            examples_text += json.dumps({"commands": ex.commands}, indent=2)
            examples_text += "\n```\n\n"

        # Append examples to base prompt
        enhanced_prompt = base_prompt + examples_text

        return enhanced_prompt

    def save_system_prompt(self, prompt: str):
        """Save a new system prompt to file"""
        self.system_prompt_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.system_prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Clear cache
        self._base_prompt = None

    def format_user_message(
        self,
        intent: str,
        context: Optional[dict] = None
    ) -> str:
        """
        Format user intent into a clear message for the LLM.

        Args:
            intent: What the user wants to do
            context: Optional context (current URL, page state, etc.)

        Returns:
            Formatted user message
        """
        message = intent

        if context:
            context_str = "\n\nContext:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            message += context_str

        return message


# Module-level instance
_default_manager: Optional[PromptManager] = None


def get_prompt_manager(
    system_prompt_path: str = "data/prompts/system_prompt.txt"
) -> PromptManager:
    """Get or create the default prompt manager instance"""
    global _default_manager
    if _default_manager is None or _default_manager.system_prompt_path != Path(system_prompt_path):
        _default_manager = PromptManager(system_prompt_path)
    return _default_manager
