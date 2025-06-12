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
from app.middleware import PerformanceMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Log settings on startup
settings = get_settings()
logger.info("=== APPLICATION SETTINGS ===")
logger.info(f"Model: {settings.llm_model}")
logger.info(f"Base URL: {settings.llm_base_url}")
logger.info(f"API Key: {'*' * 10 + settings.llm_api_key.get_secret_value()[-4:]}")
logger.info(f"Temperature: {settings.llm_temperature}")
logger.info(f"Max tokens: {settings.llm_max_tokens}")
logger.info(f"System prompt: {settings.llm_system_prompt}")
logger.info("==============================")

app = FastAPI(
    title="LLM Chatbot API",
    version="0.1.0",
    description="""
    🤖 **Modern Asynchronous LLM Chatbot API**

    A high-performance REST API for interacting with various OpenAI-compatible LLM providers.
    Built with FastAPI, featuring comprehensive error handling, retry mechanisms, and performance monitoring.

    ## 🚀 Supported Providers
    - **OpenAI** (GPT-4, GPT-3.5)
    - **Ollama** (local models)
    - **Mistral AI**
    - **Groq**
    - **Google Gemini**
    - **Anthropic Claude** (via proxy)
    - Any OpenAI-compatible APIs

    ## 📊 Features
    - Asynchronous request processing
    - Automatic retry with exponential backoff
    - Built-in performance monitoring
    - Request/response validation
    - Comprehensive error handling
    """,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.example.com", "description": "Production server"},
    ],
)

# Добавляем middleware для профилирования
app.add_middleware(PerformanceMiddleware)


# Dependency setup
async def get_llm_client() -> AsyncGenerator[LLMClient, None]:
    async with llm_client_lifespan(get_settings()) as client:
        yield client


@app.post(
    "/question",
    response_model=Answer,
    tags=["Chat"],
    summary="Ask a question to the LLM",
    description="Send a question to the configured LLM model and receive an AI-generated response.",
    responses={
        200: {
            "description": "Successful response from LLM",
            "content": {
                "application/json": {
                    "example": {
                        "text": "Hello! I'm an AI assistant. How can I help you today?"
                    }
                }
            },
            "headers": {
                "X-Process-Time": {
                    "description": "Request processing time in seconds",
                    "schema": {"type": "number", "example": 2.1543},
                },
                "X-Memory-Used": {
                    "description": "Memory usage in MB",
                    "schema": {"type": "number", "example": 78.5},
                },
                "X-Memory-Delta": {
                    "description": "Memory change in MB",
                    "schema": {"type": "number", "example": 1.2},
                },
            },
        },
        401: {
            "description": "Authentication failed with LLM provider",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication failed with LLM provider"}
                }
            },
        },
        422: {
            "description": "Validation error (e.g., empty or too long text)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "text"],
                                "msg": "String should have at least 1 character",
                                "type": "string_too_short",
                            }
                        ]
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded, try again later",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded, please try again later"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Internal server error occurred"}
                }
            },
        },
        502: {
            "description": "Invalid response from LLM provider",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid response from LLM provider"}
                }
            },
        },
    },
)
async def ask_question(
    q: Question,
    llm: LLMClient = Depends(get_llm_client),
) -> Answer:
    """
    Send a question to the configured LLM model and receive an AI-generated response.

    This endpoint processes user questions asynchronously and returns AI-generated responses.
    It includes automatic retry mechanisms, performance monitoring, and comprehensive error handling.

    The endpoint supports various LLM providers (OpenAI, Ollama, Mistral, Groq, Gemini, etc.)
    configured via environment variables.
    """
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


@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    description="Check if the API service is healthy and running",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:45.123456",
                        "service": "llm-chatbot-api",
                    }
                }
            },
        }
    },
)
async def health_check():
    """
    Health check endpoint for monitoring service availability.

    Returns the current status, timestamp, and service identifier.
    This endpoint can be used by load balancers, monitoring systems,
    and orchestration platforms to determine service health.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "llm-chatbot-api",
    }


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect to Swagger UI."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
