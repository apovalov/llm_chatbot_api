# default "just" task when no arguments are provided
default: server

# ────────────────────────────────────────
# Start the dev server (hot reload)
server:
    uv run uvicorn app.main:app --reload

# Run unit tests
test:
    PYTHONPATH=. uv run pytest

# Static analysis + autoformat
lint:
    ruff check .
    ruff format --check .
