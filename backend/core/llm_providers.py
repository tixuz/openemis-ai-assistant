"""
LLM Provider Abstraction Layer

Supports multiple LLM providers:
- Local LLM (llama.cpp server)
- Claude API (Anthropic)
- Gemini API (Google)
- OpenAI API (ChatGPT)
"""
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout


class LLMProviderError(Exception):
    """Raised when LLM provider communication fails"""
    pass


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - generate_json() - Generate JSON response from messages
    - test_connection() - Test if provider is accessible
    """

    def __init__(self, timeout: int = 180):
        self.timeout = timeout

    @abstractmethod
    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate JSON response from messages.

        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            JSON string from LLM

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if provider is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        pass


class LocalLLMProvider(BaseLLMProvider):
    """
    Local LLM provider using llama.cpp server.

    Compatible with any OpenAI-compatible local server.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8080/v1/chat/completions",
        timeout: int = 180
    ):
        super().__init__(timeout)
        self.server_url = server_url

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:
        """Generate JSON using local llama.cpp server"""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            messages,
            temperature,
            max_tokens
        )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Synchronous request to local server"""
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content

        except RequestException as e:
            raise LLMProviderError(f"Local LLM request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid response format: {e}")

    def test_connection(self) -> bool:
        """Test local LLM server"""
        try:
            # Try to get health endpoint or make minimal request
            health_url = self.server_url.replace("/v1/chat/completions", "/health")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                return True

            # Fallback: try minimal request
            response = requests.post(
                self.server_url,
                json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


class ClaudeProvider(BaseLLMProvider):
    """
    Claude API provider (Anthropic).

    Uses the Messages API with JSON mode via prompt engineering.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 60
    ):
        super().__init__(timeout)
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:
        """Generate JSON using Claude API"""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            messages,
            temperature,
            max_tokens
        )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Synchronous request to Claude API"""
        # Convert messages format
        # Extract system message
        system_content = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                user_messages.append(msg)

        # Add JSON instruction to system prompt
        if system_content:
            system_content += "\n\nIMPORTANT: Respond ONLY with valid JSON. No explanations outside the JSON."

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_content,
            "messages": user_messages
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data["content"][0]["text"]
            return content

        except RequestException as e:
            raise LLMProviderError(f"Claude API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid Claude response format: {e}")

    def test_connection(self) -> bool:
        """Test Claude API connection"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                },
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.

    Uses the Gemini API with JSON mode.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout: int = 60
    ):
        super().__init__(timeout)
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:
        """Generate JSON using Gemini API"""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            messages,
            temperature,
            max_tokens
        )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Synchronous request to Gemini API"""
        # Convert messages to Gemini format
        contents = []
        system_instruction = ""

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

        # Add JSON instruction
        if system_instruction:
            system_instruction += "\n\nRespond ONLY with valid JSON."

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"  # JSON mode
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return content

        except RequestException as e:
            raise LLMProviderError(f"Gemini API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid Gemini response format: {e}")

    def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": "test"}]}],
                    "generationConfig": {"maxOutputTokens": 10}
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider (ChatGPT).

    Uses the Chat Completions API with JSON mode.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: int = 60
    ):
        super().__init__(timeout)
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:
        """Generate JSON using OpenAI API"""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            messages,
            temperature,
            max_tokens
        )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Synchronous request to OpenAI API"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content

        except RequestException as e:
            raise LLMProviderError(f"OpenAI API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMProviderError(f"Invalid OpenAI response format: {e}")

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


class LLMProviderFactory:
    """
    Factory for creating LLM providers based on configuration.
    """

    @staticmethod
    def create_provider(
        provider_type: str,
        config: Dict[str, Any]
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_type: One of "local", "claude", "gemini", "openai"
            config: Provider-specific configuration

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider_type is unknown
        """
        if provider_type == "local":
            return LocalLLMProvider(
                server_url=config.get("server_url", "http://localhost:8080/v1/chat/completions"),
                timeout=config.get("timeout", 180)
            )

        elif provider_type == "claude":
            return ClaudeProvider(
                api_key=config["api_key"],
                model=config.get("model", "claude-3-5-sonnet-20241022"),
                timeout=config.get("timeout", 60)
            )

        elif provider_type == "gemini":
            return GeminiProvider(
                api_key=config["api_key"],
                model=config.get("model", "gemini-1.5-flash"),
                timeout=config.get("timeout", 60)
            )

        elif provider_type == "openai":
            return OpenAIProvider(
                api_key=config["api_key"],
                model=config.get("model", "gpt-4o-mini"),
                timeout=config.get("timeout", 60)
            )

        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
