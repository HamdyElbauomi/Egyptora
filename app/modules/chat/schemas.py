"""Request/response shapes for chat. Owner: Person 3."""

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
