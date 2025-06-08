from pydantic import BaseModel, Field


class Answer(BaseModel):
    """Answer sent to the client."""

    text: str = Field(..., description="Generated LLM answer")
