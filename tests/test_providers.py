"""Tests for different OpenAI-compatible providers."""

import pytest
from unittest.mock import AsyncMock
from openai import RateLimitError, InternalServerError, AuthenticationError

from app.settings import Settings
from app.clients.llm import LLMClient


@pytest.mark.parametrize(
    "provider_name,base_url,model,api_key",
    [
        ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini", "sk-test"),
        ("Ollama", "http://localhost:11434/v1", "llama3.2", "ollama"),
        ("Mistral", "https://api.mistral.ai/v1", "mistral-small-latest", "test-key"),
        (
            "Groq",
            "https://api.groq.com/openai/v1",
            "llama-3.1-70b-versatile",
            "gsk_test",
        ),
        ("LocalAI", "http://localhost:8080/v1", "ggml-gpt4all-j", "not-needed"),
    ],
)
async def test_different_providers_settings(provider_name, base_url, model, api_key):
    """Test that settings are correctly configured for different providers."""

    # Create settings for specific provider
    settings = Settings(
        llm_base_url=base_url,
        llm_model=model,
        llm_api_key=api_key,
        llm_temperature=0.7,
        llm_max_tokens=1000,
    )

    # Check that settings are correctly set
    assert settings.llm_base_url == base_url
    assert settings.llm_model == model
    assert settings.llm_api_key.get_secret_value() == api_key
    assert settings.llm_temperature == 0.7
    assert settings.llm_max_tokens == 1000


async def test_llm_client_with_settings():
    """Test that LLMClient correctly uses settings."""

    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_max_tokens=500,
    )

    # Mock AsyncOpenAI client
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    # Create LLM client
    llm_client = LLMClient(mock_client, settings)

    # Test request
    response = await llm_client.ask("Test question")

    # Check that correct parameters are used
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test question"}],
        temperature=0.5,
        max_tokens=500,
    )

    assert response == "Test response"


async def test_optional_max_tokens():
    """Test that max_tokens is an optional parameter."""

    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_max_tokens=None,  # Don't set max_tokens
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm_client = LLMClient(mock_client, settings)
    await llm_client.ask("Test question")

    # Check that max_tokens is not passed if value is not set
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test question"}],
        temperature=0.5,
    )


async def test_retry_on_rate_limit_error():
    """Test that retry happens on RateLimitError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Create mock for response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # First two calls generate RateLimitError, third is successful
    mock_success_response = AsyncMock()
    mock_success_response.choices = [
        AsyncMock(message=AsyncMock(content="Success after retry"))
    ]

    mock_client.chat.completions.create.side_effect = [
        RateLimitError("Rate limit exceeded", response=mock_response_obj, body=None),
        RateLimitError("Rate limit exceeded", response=mock_response_obj, body=None),
        mock_success_response,
    ]

    llm_client = LLMClient(mock_client, settings)
    response = await llm_client.ask("Test question")

    # Check that there were 3 attempts and successful response received
    assert mock_client.chat.completions.create.call_count == 3
    assert response == "Success after retry"


async def test_retry_on_internal_server_error():
    """Test that retry happens on InternalServerError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Create mock for response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # First call generates InternalServerError, second is successful
    mock_success_response = AsyncMock()
    mock_success_response.choices = [
        AsyncMock(message=AsyncMock(content="Success after retry"))
    ]

    mock_client.chat.completions.create.side_effect = [
        InternalServerError(
            "Internal server error", response=mock_response_obj, body=None
        ),
        mock_success_response,
    ]

    llm_client = LLMClient(mock_client, settings)
    response = await llm_client.ask("Test question")

    # Check that there were 2 attempts and successful response received
    assert mock_client.chat.completions.create.call_count == 2
    assert response == "Success after retry"


async def test_no_retry_on_authentication_error():
    """Test that retry does NOT happen on AuthenticationError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Create mock for response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # Generate AuthenticationError - retry should not happen
    auth_error = AuthenticationError(
        "Invalid API key", response=mock_response_obj, body=None
    )
    mock_client.chat.completions.create.side_effect = [auth_error]

    llm_client = LLMClient(mock_client, settings)

    # Expect that exception is raised immediately without retry
    with pytest.raises(AuthenticationError):
        await llm_client.ask("Test question")

    # Check that there was only one attempt
    assert mock_client.chat.completions.create.call_count == 1


async def test_retry_exhausted_raises_original_error():
    """Test that original error is raised after retry exhaustion."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Create mock for response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # All attempts end with RateLimitError (using list instead of single exception)
    rate_limit_error = RateLimitError(
        "Rate limit exceeded", response=mock_response_obj, body=None
    )
    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        rate_limit_error,
        rate_limit_error,
    ]

    llm_client = LLMClient(mock_client, settings)

    # Expect that RateLimitError is raised after 3 attempts
    with pytest.raises(RateLimitError):
        await llm_client.ask("Test question")

    # Check that there were exactly 3 attempts
    assert mock_client.chat.completions.create.call_count == 3


async def test_system_prompt_is_used():
    """Test that system prompt is added to messages when specified."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_system_prompt="You are a helpful assistant.",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm_client = LLMClient(mock_client, settings)
    await llm_client.ask("Test question")

    # Check that system prompt is added to messages
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test question"},
        ],
        temperature=0.5,
    )


async def test_no_system_prompt_when_not_set():
    """Test that system prompt is not added when not specified."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_system_prompt=None,  # Explicitly don't set
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm_client = LLMClient(mock_client, settings)
    await llm_client.ask("Test question")

    # Check that only user message is present
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Test question"},
        ],
        temperature=0.5,
    )


async def test_empty_system_prompt_not_used():
    """Test that empty system prompt is not added."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_system_prompt="",  # Empty string
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm_client = LLMClient(mock_client, settings)
    await llm_client.ask("Test question")

    # Check that only user message is present (empty string is considered falsy)
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Test question"},
        ],
        temperature=0.5,
    )
