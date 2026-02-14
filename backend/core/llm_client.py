"""
LLM Client - Request Structured Output from Multiple LLM Providers

This client ensures the LLM returns JSON commands, not executable Python code.
Supports Local LLM, Claude, Gemini, and OpenAI.
Includes retry logic, timeout handling, and error recovery.
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout

from backend.core.command_parser import CommandParser, ParseError
from backend.models.commands import Command
from backend.core.llm_providers import (
    BaseLLMProvider,
    LLMProviderFactory,
    LLMProviderError
)
from backend.models.llm_config import get_llm_config_store


class LLMError(Exception):
    """Raised when LLM communication fails"""
    pass


class LLMClient:
    """
    Client for communicating with LLM providers.

    Requests structured JSON output instead of executable code.
    Automatically uses configured provider (Local/Claude/Gemini/OpenAI).
    """

    def __init__(
        self,
        server_url: Optional[str] = None,  # For backward compatibility
        timeout: int = 180,
        max_retries: int = 3,
        provider: Optional[BaseLLMProvider] = None  # Override provider
    ):
        self.max_retries = max_retries
        self.parser = CommandParser()

        # Use provided provider or load from config
        if provider:
            self.provider = provider
        else:
            # Load from configuration
            config_store = get_llm_config_store()
            llm_config = config_store.load_config()

            # Override server_url for local provider if provided
            if server_url and llm_config.provider == "local":
                llm_config.server_url = server_url

            # Create provider from config
            self.provider = LLMProviderFactory.create_provider(
                provider_type=llm_config.provider,
                config=llm_config.get_provider_dict()
            )

    async def generate_commands(
        self,
        user_intent: str,
        system_prompt: str,
        examples: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> List[Command]:
        """
        Generate automation commands from user intent.

        Args:
            user_intent: What the user wants to do
            system_prompt: System instructions for the LLM
            examples: Optional list of example tasks for few-shot learning
            temperature: LLM temperature (lower = more deterministic)

        Returns:
            List of validated Command objects

        Raises:
            LLMError: If LLM communication fails
            ParseError: If LLM output cannot be parsed
        """
        # Build messages
        messages = self._build_messages(user_intent, system_prompt, examples)

        # Request JSON from LLM with retry logic
        response_text = await self._request_with_retry(messages, temperature)

        # Parse and validate commands
        try:
            commands = self.parser.parse(response_text)
            return commands
        except ParseError as e:
            # Try to recover from common errors
            recovery_prompt = self._build_recovery_prompt(response_text, str(e))
            recovery_messages = messages + [
                {"role": "assistant", "content": response_text},
                {"role": "user", "content": recovery_prompt}
            ]

            # One retry with recovery prompt
            recovery_text = await self._request_with_retry(recovery_messages, temperature)
            return self.parser.parse(recovery_text)

    def _build_messages(
        self,
        user_intent: str,
        system_prompt: str,
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build messages array for LLM request"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add examples for few-shot learning
        if examples:
            for example in examples:
                messages.append({
                    "role": "user",
                    "content": example.get("task_description", "")
                })
                messages.append({
                    "role": "assistant",
                    "content": json.dumps({"commands": example.get("commands", [])})
                })

        # Add current user intent
        messages.append({
            "role": "user",
            "content": user_intent
        })

        return messages

    def _build_recovery_prompt(self, failed_output: str, error: str) -> str:
        """Build a recovery prompt when parsing fails"""
        return f"""Your previous response could not be parsed: {error}

Please try again. Remember:
1. Output ONLY valid JSON
2. Use the "commands" array format
3. Each command must have a "type" field
4. Do not include explanations outside the JSON

Example format:
{{
  "commands": [
    {{"type": "navigate", "url": "https://demo.openemis.org"}},
    {{"type": "fill", "selector": "#username", "value": "admin"}}
  ]
}}
"""

    async def _request_with_retry(
        self,
        messages: List[Dict[str, str]],
        temperature: float
    ) -> str:
        """
        Make LLM request with exponential backoff retry.

        Args:
            messages: Messages array
            temperature: LLM temperature

        Returns:
            LLM response text

        Raises:
            LLMError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Use provider to generate response
                response_text = await self.provider.generate_json(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=2000
                )
                return response_text

            except (LLMProviderError, RequestException, Timeout) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                continue

        raise LLMError(f"LLM request failed after {self.max_retries} attempts: {last_error}")

    def test_connection(self) -> bool:
        """
        Test if LLM provider is reachable.

        Returns:
            True if provider responds, False otherwise
        """
        return self.provider.test_connection()


# Module-level convenience function

async def generate_commands_from_intent(
    user_intent: str,
    system_prompt: str,
    server_url: str = "http://localhost:8080/v1/chat/completions",
    examples: Optional[List[Dict[str, Any]]] = None
) -> List[Command]:
    """
    Convenience function to generate commands from user intent.

    Args:
        user_intent: What the user wants to do
        system_prompt: System instructions
        server_url: LLM server URL
        examples: Optional few-shot examples

    Returns:
        List of validated Command objects
    """
    client = LLMClient(server_url=server_url)
    return await client.generate_commands(user_intent, system_prompt, examples)
