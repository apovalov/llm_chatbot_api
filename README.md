# LLM Chatbot API

Асинхронный REST API для работы с различными OpenAI-совместимыми LLM провайдерами.

## 🚀 Поддерживаемые провайдеры

- **OpenAI** (GPT-4, GPT-3.5)
- **Ollama** (локальные модели)
- **Mistral AI**
- **Groq**
- **LocalAI** (самохостинг)
- **Google Gemini** (через OpenAI-compatible endpoint)
- **Anthropic Claude** (через прокси)
- Любые другие OpenAI-compatible API

## ⚙️ Настройка

### 1. Установка зависимостей

```bash
uv sync
```

### 2. Конфигурация

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

### 3. Настройка провайдеров

#### OpenAI (по умолчанию)
```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-your-openai-api-key
```

#### Ollama (локальный)
```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
LLM_API_KEY=ollama
```

#### Mistral AI
```env
LLM_BASE_URL=https://api.mistral.ai/v1
LLM_MODEL=mistral-small-latest
LLM_API_KEY=your-mistral-api-key
```

#### Groq
```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-70b-versatile
LLM_API_KEY=your-groq-api-key
```

### 4. Дополнительные параметры

```env
# Температура генерации (0.0 - 2.0)
LLM_TEMPERATURE=0.7

# Максимальное количество токенов (опционально)
LLM_MAX_TOKENS=1000

# Таймаут запросов (секунды)
REQUEST_TIMEOUT=30.0
```

## 🛠️ Команды

```bash
# Запуск сервера
just server

# Запуск тестов
just test

# Проверка кода
just lint
```

## 📖 API

### POST /question

Отправка вопроса к LLM модели.

**Request:**
```json
{
  "text": "Привет! Как дела?"
}
```

**Response:**
```json
{
  "text": "Привет! У меня всё хорошо, спасибо! Как ваши дела?"
}
```

### Swagger UI

Интерактивная документация API доступна по адресу: `http://localhost:8000/docs`

## 🧪 Тестирование

Проект включает полный набор тестов:

- ✅ Валидация входных данных
- ✅ Проверка длины текста
- ✅ Мокирование LLM ответов
- ✅ Обработка ошибок API
- ✅ Тестирование разных провайдеров
- ✅ Специфичные retry логики для RateLimitError и InternalServerError
- ✅ Проверка отсутствия retry для AuthenticationError

## 🔄 Retry логика

API автоматически повторяет запросы при временных ошибках:

- **Повторы**: максимум 3 попытки
- **Задержка**: экспоненциальная (1с, 2с, 4с, 8с макс)
- **Условия**: только при `RateLimitError` и `InternalServerError`
- **Исключения**: `AuthenticationError` и другие ошибки не повторяются

## 🏗️ Архитектура

- **FastAPI** - современный веб-фреймворк
- **AsyncOpenAI** - официальный SDK для OpenAI API
- **Pydantic** - валидация данных
- **Tenacity** - умные повторные попытки запросов
- **pytest** - тестирование

