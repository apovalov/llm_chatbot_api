"""Async client for OpenAI-compatible LLM APIs."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from openai import AsyncOpenAI, RateLimitError, InternalServerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.settings import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper over OpenAI API with retry logic."""

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
        logger.info("=== LLM REQUEST ===")
        logger.info(f"Model: {self._settings.llm_model}")
        logger.info(f"Base URL: {self._settings.llm_base_url}")
        logger.info(f"Question length: {len(question)} chars")

        # Prepare messages with optional system prompt
        messages: List[Dict[str, str]] = []
        if self._settings.llm_system_prompt:
            messages.append(
                {"role": "system", "content": self._settings.llm_system_prompt}
            )
        messages.append({"role": "user", "content": question})

        # Prepare basic request parameters
        create_params: Dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
        }

        # Add max_tokens if specified
        if self._settings.llm_max_tokens is not None:
            create_params["max_tokens"] = self._settings.llm_max_tokens

        response = await self._client.chat.completions.create(**create_params)

        # Response validation
        if not response.choices:
            raise ValueError("No response choices received from LLM")

        choice = response.choices[0]
        if not choice.message or not choice.message.content:
            raise ValueError("Empty response received from LLM")

        return choice.message.content


@asynccontextmanager
async def llm_client_lifespan(settings: Settings) -> AsyncGenerator[LLMClient, None]:
    """Creates AsyncOpenAI client and returns LLMClient."""
    client = AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        timeout=settings.request_timeout,
    )

    try:
        yield LLMClient(client, settings)
    finally:
        await client.close()
