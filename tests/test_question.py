from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.schemas import Answer
from tests.test_helpers import create_mock_response


def test_ok_sync(client: TestClient, mock_openai_client) -> None:
    """Синхронный тест с моканием OpenAI."""
    with patch("app.clients.llm.AsyncOpenAI") as mock_openai_class:
        mock_openai_class.return_value = mock_openai_client

        # Используем helper функцию для создания мок ответа
        mock_openai_client.chat.completions.create.return_value = create_mock_response(
            "Echo: Hello"
        )

        resp = client.post("/question", json={"text": "Hello"})
        assert resp.status_code == 200
        assert Answer(**resp.json()).text == "Echo: Hello"


async def test_ok_async(async_client: AsyncClient, mock_openai_client) -> None:
    """Асинхронный тест с моканием OpenAI."""
    with patch("app.clients.llm.AsyncOpenAI") as mock_openai_class:
        mock_openai_class.return_value = mock_openai_client

        # Используем helper функцию для создания мок ответа
        mock_openai_client.chat.completions.create.return_value = create_mock_response(
            "Echo: Hello"
        )

        resp = await async_client.post("/question", json={"text": "Hello"})
        assert resp.status_code == 200
        assert Answer(**resp.json()).text == "Echo: Hello"


@pytest.mark.parametrize(
    "payload",
    [
        {},  # no text field
        {"text": ""},  # empty string
        {"text": "x" * 2048},  # too long
    ],
)
def test_validation_errors(client: TestClient, payload: dict) -> None:
    """Тестируем валидацию входных данных."""
    resp = client.post("/question", json=payload)
    assert resp.status_code == 422


def test_llm_error(client: TestClient, mock_openai_client) -> None:
    """Тестируем обработку ошибок от LLM API."""
    with patch("app.clients.llm.AsyncOpenAI") as mock_openai_class:
        mock_openai_class.return_value = mock_openai_client

        # Настраиваем мок для генерации ошибки
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Test LLM error"
        )

        resp = client.post("/question", json={"text": "Hello"})
        assert resp.status_code == 500
