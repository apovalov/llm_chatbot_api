from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from httpx import AsyncClient, HTTPError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas import Answer, Question
from app.settings import Settings, get_settings


app = FastAPI(title="LLM Chatbot API", version="0.1.0")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect to Swagger UI."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# ────────────────────────────────────
# HTTP client, created once
async_client: AsyncClient | None = None


async def get_client() -> AsyncClient:
    """Lazy creation of httpx.AsyncClient."""
    global async_client  # noqa: PLW0603
    if async_client is None:
        async_client = AsyncClient(timeout=get_settings().request_timeout)
    return async_client


# ────────────────────────────────────
# LLM call with retry


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
async def call_llm(question: str, settings: Settings, client: AsyncClient) -> str:
    """Send request to LLM-compatible API and return answer."""
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": question}],
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        resp = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
    except HTTPError as exc:
        # pass to tenacity, if 500 or 429, will be retry
        raise exc

    data = resp.json()
    return data["choices"][0]["message"]["content"]  # type: ignore[index]


# ────────────────────────────────────
# POST /question


@app.post(
    "/question",
    response_model=Answer,
    status_code=status.HTTP_200_OK,
    summary="Получить ответ LLM на вопрос",
)
async def ask_question(
    q: Question,
    settings: Settings = Depends(get_settings),
    client: AsyncClient = Depends(get_client),
) -> Answer:
    """Accept question, return answer from LLM."""
    try:
        answer_text = await call_llm(q.text, settings, client)
    except HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {exc}",
        ) from exc

    return Answer(text=answer_text)
