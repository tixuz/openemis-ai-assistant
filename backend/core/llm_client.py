"""
LLM Client - Request Structured Output from DeepSeek

This client ensures the LLM returns JSON commands, not executable Python code.
Includes retry logic, timeout handling, and error recovery.
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout

from backend.core.command_parser import CommandParser, ParseError
from backend.models.commands import Command


class LLMError(Exception):
    """Raised when LLM communication fails"""
    pass


class LLMClient:
    """
    Client for communicating with DeepSeek LLM server.

    Requests structured JSON output instead of executable code.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8080/v1/chat/completions",
        timeout: int = 180,  # 3 minutes for CPU inference
        max_retries: int = 3
    ):
        self.server_url = server_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.parser = CommandParser()

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
                # Run synchronous request in thread pool
                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(
                    None,
                    self._make_request,
                    messages,
                    temperature
                )
                return response_text

            except (RequestException, Timeout) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                continue

        raise LLMError(f"LLM request failed after {self.max_retries} attempts: {last_error}")

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float
    ) -> str:
        """
        Make synchronous HTTP request to LLM server.

        This runs in a thread pool via asyncio.run_in_executor
        """
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
            # Request JSON format if supported by DeepSeek
            # "response_format": {"type": "json_object"}  # Uncomment if supported
        }

        try:
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Extract content from response
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return content
            else:
                raise LLMError(f"Unexpected LLM response format: {data}")

        except RequestException as e:
            raise LLMError(f"HTTP request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Failed to extract content from response: {e}")

    def test_connection(self) -> bool:
        """
        Test if LLM server is reachable.

        Returns:
            True if server responds, False otherwise
        """
        try:
            response = requests.post(
                self.server_url,
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


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
