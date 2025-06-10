"""Асинхронный клиент для OpenAI-совместимых LLM API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from openai import AsyncOpenAI, RateLimitError, InternalServerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.settings import Settings


class LLMClient:
    """Обертка над OpenAI API с логикой повторных попыток."""

    def __init__(self, client: AsyncOpenAI, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((RateLimitError, InternalServerError)),
        reraise=True,
    )
    async def ask(self, question: str) -> str:
        # Подготавливаем базовые параметры запроса
        create_params = {
            "model": self._settings.llm_model,
            "messages": [{"role": "user", "content": question}],
            "temperature": self._settings.llm_temperature,
        }

        # Добавляем max_tokens если указан
        if self._settings.llm_max_tokens:
            create_params["max_tokens"] = self._settings.llm_max_tokens

        response = await self._client.chat.completions.create(
            model=create_params["model"],
            messages=create_params["messages"],  # type: ignore
            temperature=create_params["temperature"],
            max_tokens=create_params.get("max_tokens"),
        )

        # Валидация ответа
        if not response.choices:
            raise ValueError("No response choices received from LLM")

        choice = response.choices[0]
        if not choice.message or not choice.message.content:
            raise ValueError("Empty response received from LLM")

        return choice.message.content


@asynccontextmanager
async def llm_client_lifespan(settings: Settings) -> AsyncGenerator[LLMClient, None]:
    """Создает AsyncOpenAI клиент и возвращает LLMClient."""
    client = AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        timeout=settings.request_timeout,
    )

    try:
        yield LLMClient(client, settings)
    finally:
        await client.close()
