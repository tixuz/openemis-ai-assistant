"""
LLM Configuration Models

Stores LLM provider settings with encrypted API keys.
"""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
import json
import base64
from pathlib import Path


class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM provider"""

    provider: Literal["local", "claude", "gemini", "openai"] = Field(
        description="LLM provider type"
    )

    # Local provider settings
    server_url: Optional[str] = Field(
        default="http://host.docker.internal:8080/v1/chat/completions",
        description="URL for local LLM server (use host.docker.internal from Docker)"
    )

    # API provider settings
    api_key: Optional[str] = Field(
        default=None,
        description="API key for cloud providers (encrypted in storage)"
    )

    model: Optional[str] = Field(
        default=None,
        description="Model name/ID to use"
    )

    timeout: int = Field(
        default=180,
        ge=10,
        le=600,
        description="Request timeout in seconds"
    )

    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=4000,
        description="Maximum tokens to generate"
    )

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )

    enabled: bool = Field(
        default=True,
        description="Whether this provider is enabled"
    )

    @validator("api_key")
    def validate_api_key(cls, v, values):
        """API key required for cloud providers"""
        provider = values.get("provider")
        if provider in ["claude", "gemini", "openai"] and not v:
            raise ValueError(f"API key required for {provider} provider")
        return v

    @validator("model")
    def set_default_model(cls, v, values):
        """Set default model based on provider"""
        if v:
            return v

        provider = values.get("provider")
        defaults = {
            "claude": "claude-3-5-sonnet-20241022",
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o-mini"
        }
        return defaults.get(provider)

    def get_provider_dict(self) -> Dict[str, Any]:
        """Get configuration as dict for provider initialization"""
        config = {
            "timeout": self.timeout
        }

        if self.provider == "local":
            config["server_url"] = self.server_url

        elif self.provider in ["claude", "gemini", "openai"]:
            config["api_key"] = self.api_key
            if self.model:
                config["model"] = self.model

        return config


class LLMConfigStore:
    """
    Store and retrieve LLM configuration.

    Saves to data/llm_config.json with basic encryption for API keys.
    """

    def __init__(self, config_file: str = "data/llm_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Simple XOR key for basic obfuscation (not cryptographically secure!)
        # In production, use proper encryption (cryptography.fernet)
        self._xor_key = b"ai-automation-secret-key-2024"

    def _encrypt_key(self, api_key: str) -> str:
        """Basic XOR encryption for API key"""
        if not api_key:
            return ""

        key_bytes = api_key.encode()
        xor_key = self._xor_key
        encrypted = bytes([b ^ xor_key[i % len(xor_key)] for i, b in enumerate(key_bytes)])
        return base64.b64encode(encrypted).decode()

    def _decrypt_key(self, encrypted: str) -> str:
        """Basic XOR decryption for API key"""
        if not encrypted:
            return ""

        encrypted_bytes = base64.b64decode(encrypted.encode())
        xor_key = self._xor_key
        decrypted = bytes([b ^ xor_key[i % len(xor_key)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode()

    def save_config(self, config: LLMProviderConfig):
        """Save LLM configuration to file"""
        data = config.model_dump()

        # Encrypt API key before saving
        if data.get("api_key"):
            data["api_key"] = self._encrypt_key(data["api_key"])

        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_config(self) -> Optional[LLMProviderConfig]:
        """Load LLM configuration from file"""
        if not self.config_file.exists():
            # Return default local config
            return LLMProviderConfig(provider="local")

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            # Decrypt API key
            if data.get("api_key"):
                data["api_key"] = self._decrypt_key(data["api_key"])

            return LLMProviderConfig(**data)

        except Exception as e:
            print(f"Error loading LLM config: {e}")
            # Return default on error
            return LLMProviderConfig(provider="local")

    def delete_config(self):
        """Delete configuration file"""
        if self.config_file.exists():
            self.config_file.unlink()


# Global instance
_config_store = None


def get_llm_config_store() -> LLMConfigStore:
    """Get global LLM config store instance"""
    global _config_store
    if _config_store is None:
        _config_store = LLMConfigStore()
    return _config_store
