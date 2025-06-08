from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

app = FastAPI(title="LLM Chatbot API", version="0.1.0")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect to Swagger UI."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
