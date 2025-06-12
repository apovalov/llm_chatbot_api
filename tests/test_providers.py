"""Тесты для разных OpenAI-совместимых провайдеров."""

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
    """Тестируем что настройки правильно конфигурируются для разных провайдеров."""

    # Создаем настройки для конкретного провайдера
    settings = Settings(
        llm_base_url=base_url,
        llm_model=model,
        llm_api_key=api_key,
        llm_temperature=0.7,
        llm_max_tokens=1000,
    )

    # Проверяем что настройки правильно установлены
    assert settings.llm_base_url == base_url
    assert settings.llm_model == model
    assert settings.llm_api_key.get_secret_value() == api_key
    assert settings.llm_temperature == 0.7
    assert settings.llm_max_tokens == 1000


async def test_llm_client_with_settings():
    """Тестируем что LLMClient правильно использует настройки."""

    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_max_tokens=500,
    )

    # Мокаем AsyncOpenAI клиент
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    # Создаем LLM клиент
    llm_client = LLMClient(mock_client, settings)

    # Тестируем запрос
    response = await llm_client.ask("Test question")

    # Проверяем что используются правильные параметры
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test question"}],
        temperature=0.5,
        max_tokens=500,
    )

    assert response == "Test response"


async def test_optional_max_tokens():
    """Тестируем что max_tokens является опциональным параметром."""

    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
        llm_max_tokens=None,  # Не устанавливаем max_tokens
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm_client = LLMClient(mock_client, settings)
    await llm_client.ask("Test question")

    # Проверяем что max_tokens не передается, если значение не задано
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test question"}],
        temperature=0.5,
    )


async def test_retry_on_rate_limit_error():
    """Тестируем что retry происходит при RateLimitError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Создаем мок для response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # Первые два вызова генерируют RateLimitError, третий успешен
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

    # Проверяем что было 3 попытки и получен успешный ответ
    assert mock_client.chat.completions.create.call_count == 3
    assert response == "Success after retry"


async def test_retry_on_internal_server_error():
    """Тестируем что retry происходит при InternalServerError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Создаем мок для response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # Первый вызов генерирует InternalServerError, второй успешен
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

    # Проверяем что было 2 попытки и получен успешный ответ
    assert mock_client.chat.completions.create.call_count == 2
    assert response == "Success after retry"


async def test_no_retry_on_authentication_error():
    """Тестируем что retry НЕ происходит при AuthenticationError."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Создаем мок для response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # Генерируем AuthenticationError - retry не должен происходить
    auth_error = AuthenticationError(
        "Invalid API key", response=mock_response_obj, body=None
    )
    mock_client.chat.completions.create.side_effect = [auth_error]

    llm_client = LLMClient(mock_client, settings)

    # Ожидаем что исключение поднимется сразу без retry
    with pytest.raises(AuthenticationError):
        await llm_client.ask("Test question")

    # Проверяем что была только одна попытка
    assert mock_client.chat.completions.create.call_count == 1


async def test_retry_exhausted_raises_original_error():
    """Тестируем что после исчерпания retry поднимается оригинальная ошибка."""
    settings = Settings(
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4o-mini",
        llm_api_key="test",
        llm_temperature=0.5,
    )

    mock_client = AsyncMock()

    # Создаем мок для response
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()

    # Все попытки завершаются RateLimitError (используем список вместо одиночного исключения)
    rate_limit_error = RateLimitError(
        "Rate limit exceeded", response=mock_response_obj, body=None
    )
    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        rate_limit_error,
        rate_limit_error,
    ]

    llm_client = LLMClient(mock_client, settings)

    # Ожидаем что после 3 попыток поднимется RateLimitError
    with pytest.raises(RateLimitError):
        await llm_client.ask("Test question")

    # Проверяем что было ровно 3 попытки
    assert mock_client.chat.completions.create.call_count == 3
