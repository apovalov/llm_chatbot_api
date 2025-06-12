from pydantic import BaseModel, Field


class Question(BaseModel):
    """
    User question model for LLM interaction.

    This model represents a question or prompt sent by the user to the LLM.
    The text is validated for length constraints to ensure reasonable API usage
    and prevent abuse.
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="User question or prompt text. Must be between 1 and 1024 characters.",
        examples=[
            "Hello! How are you?",
            "Explain quantum computing in simple terms",
            "Write a Python function to calculate fibonacci numbers",
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "What is artificial intelligence?"},
                {
                    "text": "Help me write a cover letter for a software engineer position"
                },
                {"text": "Explain the difference between REST and GraphQL APIs"},
            ]
        }
    }
