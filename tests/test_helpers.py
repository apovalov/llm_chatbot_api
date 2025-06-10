"""Helper функции для тестов."""

from unittest.mock import AsyncMock, Mock


def create_mock_response(content: str):
    """Создает мок ответа OpenAI.

    Args:
        content: Содержимое ответа

    Returns:
        AsyncMock объект, имитирующий ответ OpenAI API
    """
    mock_response = AsyncMock()
    mock_message = Mock()
    mock_message.content = content
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


def create_mock_error_response():
    """Создает мок объект ответа для ошибок.

    Returns:
        AsyncMock объект для использования в исключениях OpenAI
    """
    mock_response_obj = AsyncMock()
    mock_response_obj.request = AsyncMock()
    return mock_response_obj


def create_mock_openai_client(default_response_content: str = "Echo: test message"):
    """Создает полностью настроенный мок AsyncOpenAI клиента.

    Args:
        default_response_content: Содержимое ответа по умолчанию

    Returns:
        Mock объект, имитирующий AsyncOpenAI клиент
    """
    mock = Mock()

    # Мокаем структуру chat.completions.create как AsyncMock
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = AsyncMock()

    # Настраиваем мок для успешного ответа
    mock.chat.completions.create.return_value = create_mock_response(
        default_response_content
    )
    mock.close = AsyncMock()

    return mock
