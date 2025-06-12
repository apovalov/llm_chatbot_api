from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app as fastapi_app
from tests.test_helpers import create_mock_openai_client


@pytest.fixture
def mock_openai_client():
    """Mock AsyncOpenAI client."""
    return create_mock_openai_client()


@pytest.fixture
def client():
    """Create synchronous test client for FastAPI."""
    return TestClient(fastapi_app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client for FastAPI."""
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac
