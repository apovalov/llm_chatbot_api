from pydantic import BaseModel, Field


class Question(BaseModel):
    """Question received from the client."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=1_024,
        description="User question text",
    )
