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
