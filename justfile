# default "just" task when no arguments are provided
default: server

# ────────────────────────────────────────
# Start the dev server (hot reload)
server:
    uv run uvicorn app.main:app --reload

# Run unit tests
test:
    uv run pytest

# Static analysis + autoformat
lint:
    ruff check .
    ruff format --check .

# ────────────────────────────────────────
# Load testing with Locust
loadtest-start:
    uv run locust --host=http://localhost:8000

# Quick load test (10 users for 30 seconds)
loadtest-quick:
    uv run locust --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 30s --headless --csv=results/quick

# Heavy load test (50 users for 2 minutes)
loadtest-heavy:
    uv run locust --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 2m --headless --csv=results/heavy --html=results/heavy-report.html

# Stress test (100 users)
loadtest-stress:
    uv run locust --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless --csv=results/stress --html=results/stress-report.html

# ────────────────────────────────────────
# Performance profiling
profile-benchmark:
    uv run python benchmark.py

# Memory profiling
profile-memory:
    uv run python -m memory_profiler memory_profiler.py

# CPU profiling with py-spy (requires server PID)
profile-cpu PID:
    uv run py-spy record -o results/cpu_profile.svg -d 30 -p {{PID}}

# Full system profiling
profile-full:
    #!/usr/bin/env bash
    echo "🚀 Запуск полного профилирования..."
    echo "1. Запускаем benchmark..."
    uv run python benchmark.py
    echo "2. Профилирование памяти..."
    uv run python -m memory_profiler memory_profiler.py
    echo "✅ Профилирование завершено!"

# ────────────────────────────────────────
# Docker commands
docker-build:
    docker build -t llm-chatbot-api .

# Build and run in production mode
docker-run:
    docker-compose up --build

# Run in development mode with hot reload
docker-dev:
    docker-compose --profile dev up --build api-dev

# Run with caching (Redis)
docker-cache:
    docker-compose --profile cache up --build

# Run with reverse proxy
docker-proxy:
    docker-compose --profile proxy up --build

# Stop all containers
docker-stop:
    docker-compose down

# Clean up containers and images
docker-clean:
    docker-compose down --volumes --rmi all
    docker system prune -f

# View logs
docker-logs SERVICE="api":
    docker-compose logs -f {{SERVICE}}

# Run tests in Docker
docker-test:
    docker build --target builder -t llm-chatbot-api:test .
    docker run --rm llm-chatbot-api:test uv run pytest

# Shell into running container
docker-shell:
    docker exec -it llm-chatbot-api /bin/bash
