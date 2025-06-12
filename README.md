# LLM Chatbot API

Asynchronous REST API for working with various OpenAI-compatible LLM providers.

## 🚀 Supported Providers

- **OpenAI** (GPT-4, GPT-3.5)
- **Ollama** (local models)
- **Mistral AI**
- **Groq**
- **LocalAI** (self-hosted)
- **Google Gemini** (via OpenAI-compatible endpoint)
- **Anthropic Claude** (via proxy)
- Any other OpenAI-compatible APIs

## ⚙️ Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configuration

Create `.env` file based on `env.example`:

```bash
cp env.example .env
```

### 3. Provider Configuration

#### OpenAI (default)
```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-your-openai-api-key
```

#### Ollama (local)
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

### 4. Additional Parameters

```env
# System prompt for the model (optional)
LLM_SYSTEM_PROMPT="You are a helpful AI assistant. Be polite and informative in your responses."

# Generation temperature (0.0 - 2.0)
LLM_TEMPERATURE=0.7

# Maximum number of tokens (optional)
LLM_MAX_TOKENS=1000

# Request timeout (seconds)
REQUEST_TIMEOUT=30.0
```

## 🛠️ Commands

```bash
# Start server
just server

# Run tests
just test

# Check code
just lint
```

## 📖 API

### POST /question

Send a question to the LLM model.

**Request:**
```json
{
  "text": "Hello! How are you?"
}
```

**Response:**
```json
{
  "text": "Hello! I'm doing well, thank you! How are you doing?"
}
```

### Swagger UI

Interactive API documentation is available at: `http://localhost:8000/docs`

## 🧪 Testing

The project includes a comprehensive test suite:

- ✅ Input data validation
- ✅ Text length verification
- ✅ LLM response mocking
- ✅ API error handling
- ✅ Testing different providers
- ✅ Specific retry logic for RateLimitError and InternalServerError
- ✅ Verification of no retry for AuthenticationError

## 🔄 Retry Logic

API automatically retries requests on temporary errors:

- **Retries**: maximum 3 attempts
- **Delay**: exponential (1s, 2s, 4s, 8s max)
- **Conditions**: only for `RateLimitError` and `InternalServerError`
- **Exceptions**: `AuthenticationError` and other errors are not retried

## 🏗️ Architecture

- **FastAPI** - modern web framework
- **AsyncOpenAI** - official SDK for OpenAI API
- **Pydantic** - data validation
- **Tenacity** - smart request retries
- **pytest** - testing

## 📊 Load Testing

The project includes comprehensive load testing with **Locust**:

```bash
# Interactive testing with web UI
just loadtest-start

# Quick test (10 users, 30 seconds)
just loadtest-quick

# Load test (50 users, 2 minutes)
just loadtest-heavy

# Stress test (100 users, 5 minutes)
just loadtest-stress
```

### Results Summary
- **Throughput**: ~1.3 requests/second
- **Response Time**: 3-20 seconds (LLM dependent)
- **Reliability**: 0% error rate
- **Health Checks**: <5ms response time

See `LOAD_TESTING.md` for detailed instructions and `PERFORMANCE_REPORT.md` for analysis.

## 🔍 Performance Profiling

The project includes comprehensive performance profiling tools:

```bash
# Automated benchmark testing
just profile-benchmark

# Memory usage profiling
just profile-memory

# CPU profiling (requires server PID)
just profile-cpu 12345

# Full profiling suite
just profile-full
```

### Built-in Metrics
Every API response includes performance headers:
- `X-Process-Time` - Request processing time (seconds)
- `X-Memory-Used` - Memory usage (MB)
- `X-Memory-Delta` - Memory change per request (MB)

### Results Summary
- **Reliability**: 100% success rate
- **Response Time**: 2.6-13 seconds (avg: 5.95s)
- **Memory Usage**: ~78MB (stable, no leaks)
- **Bottleneck**: LLM provider response time

See `PROFILING.md` for complete documentation and `PROFILING_REPORT.md` for latest analysis.

## 📖 Enhanced API Documentation

The API features comprehensive auto-generated documentation with:

- **Interactive Swagger UI**: Available at `/docs`
- **Alternative ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

### Documentation Features
- Detailed endpoint descriptions with examples
- Request/response schemas with validation rules
- Error response specifications
- Performance monitoring headers
- Authentication requirements
- Rate limiting information

### API Endpoints
- `POST /question` - Send questions to LLM with comprehensive error handling
- `GET /health` - Health check with system status
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative documentation interface

### Response Headers
Every API response includes performance metrics:
- `X-Process-Time` - Request processing time
- `X-Memory-Used` - Current memory usage
- `X-Memory-Delta` - Memory change per request

## 🐳 Docker Containerization

Complete containerization solution with production-ready configuration:

```bash
# Quick start - Production
just docker-run

# Development with hot reload
just docker-dev

# With Redis caching
just docker-cache

# With Nginx reverse proxy
just docker-proxy
```

### Features
- **Multi-stage builds** for optimized images (~200MB)
- **Security-hardened** containers (non-root user)
- **Health checks** and monitoring
- **Development environments** with hot reload
- **Production-ready** with reverse proxy and caching
- **CI/CD integration** examples

### Deployment Options
- Standalone Docker containers
- Docker Compose for multi-service setup
- Kubernetes deployment manifests
- AWS ECS task definitions
- Nginx reverse proxy with rate limiting

See `DOCKER.md` for complete containerization guide.

