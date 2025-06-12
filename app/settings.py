"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for working with various OpenAI-compatible APIs.

    Supported providers:
    - OpenAI (default)
    - Ollama (local)
    - Mistral AI
    - Google Gemini (via OpenAI-compatible endpoint)
    - Anthropic Claude (via proxy)
    - LocalAI (self-hosted)
    - Groq
    - Any other OpenAI-compatible APIs
    """

    # OpenAI-compatible API endpoint
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI-compatible API",
    )

    # Model to use (depends on provider)
    llm_model: str = Field(
        default="gpt-4o-mini", min_length=1, description="Model name to use"
    )

    # API key (can be arbitrary for some providers)
    llm_api_key: SecretStr = Field(
        ..., min_length=1, description="API key for LLM provider"
    )

    # Maximum number of tokens in response (optional)
    llm_max_tokens: Optional[int] = Field(
        default=None, gt=0, le=100000, description="Maximum tokens in response"
    )

    # Temperature for generation (0.0 - 2.0)
    llm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for generation"
    )

    # System prompt for LLM (optional)
    llm_system_prompt: Optional[str] = Field(
        default=None,
        max_length=4096,
        description="System prompt for LLM (optional)",
    )

    # HTTP request timeout
    request_timeout: float = Field(
        default=30.0, gt=0.0, le=300.0, description="HTTP request timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("llm_base_url")
    @classmethod
    def validate_base_url(cls, v):
        """Validate that base URL is a proper HTTP/HTTPS URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        if not v.endswith("/v1"):
            raise ValueError("Base URL should end with /v1 for OpenAI compatibility")
        return v


@lru_cache
def get_settings() -> Settings:  # pragma: no cover
    """Cached singleton with settings."""
    return Settings()
