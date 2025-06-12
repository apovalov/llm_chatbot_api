"""Helper functions for tests."""

from unittest.mock import AsyncMock, Mock


def create_mock_response(content: str):
    """Creates mock OpenAI response.

    Args:
        content: Response content

    Returns:
        AsyncMock object imitating OpenAI API response
    """
    mock_response = AsyncMock()
    mock_message = Mock()
    mock_message.content = content
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


def create_mock_error_response():
    """Creates mock response object for errors.

    Returns:
        AsyncMock object for use in OpenAI exceptions
    """
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()
    return mock_response_obj


def create_mock_openai_client(default_response_content: str = "Echo: test message"):
    """Creates fully configured mock AsyncOpenAI client.

    Args:
        default_response_content: Default response content

    Returns:
        Mock object imitating AsyncOpenAI client
    """
    mock = Mock()

    # Mock chat.completions.create structure as AsyncMock
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = AsyncMock()

    # Configure mock for successful response
    mock.chat.completions.create.return_value = create_mock_response(
        default_response_content
    )
    mock.close = AsyncMock()

    return mock
