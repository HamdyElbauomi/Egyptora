"""Request/response shapes for chat. Owner: Person 3."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.trips.schemas import TripOut


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000, examples=["cheaper hotel in Luxor"])


class ChangeOut(BaseModel):
    id: int
    summary: str
    explanation: str | None
    cost_delta: int  # + more expensive, - cheaper
    status: str  # proposed | kept | undone
    day_numbers: list[int]  # days this change touches
    created_at: datetime


class MessageOut(BaseModel):
    id: int
    role: str  # user | assistant
    content: str
    change: ChangeOut | None = None
    created_at: datetime


class ChatReplyOut(BaseModel):
    message: MessageOut  # what the traveler sent
    reply: MessageOut  # the assistant's answer, with its proposed change if any


class ChangeResultOut(BaseModel):
    change: ChangeOut
    trip: TripOut
