import logging
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from collections.abc import AsyncGenerator
from openai import AuthenticationError, RateLimitError

from app.schemas import Answer, Question
from app.settings import get_settings
from app.clients.llm import LLMClient, llm_client_lifespan
from app.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(title="LLM Chatbot API", version="0.1.0")


# Dependency setup
async def get_llm_client() -> AsyncGenerator[LLMClient, None]:
    async with llm_client_lifespan(get_settings()) as client:
        yield client


@app.post("/question", response_model=Answer)
async def ask_question(
    q: Question,
    llm: LLMClient = Depends(get_llm_client),
) -> Answer:
    """Send question to LLM model."""
    logger.info(f"Received question with length: {len(q.text)}")

    try:
        answer_text = await llm.ask(q.text)
        logger.info("Successfully generated response")
        return Answer(text=answer_text)
    except AuthenticationError as exc:
        logger.error(f"Authentication failed with LLM provider: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with LLM provider",
        ) from exc
    except RateLimitError as exc:
        logger.warning(f"Rate limit exceeded: {exc}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded, please try again later",
        ) from exc
    except ValueError as exc:
        logger.error(f"Invalid response from LLM: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from LLM provider",
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during LLM request: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred",
        ) from exc


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "llm-chatbot-api",
    }


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect to Swagger UI."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
