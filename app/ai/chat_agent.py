"""AI piece: chat agent that edits the trip. Owner: Person 3.

Why: reads the trip and the traveler's message, returns one proposed change, a short explanation and its cost effect.
Then: the change is saved in trip_changes and waits for Keep or Undo.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])


class ChatIn(BaseModel):
    message: str
    trip: dict  # the full trip as returned by GET /trips/{id}
    history: list[dict] = []


class ProposedChange(BaseModel):
    summary: str
    explanation: str
    cost_delta: int
    diff: dict  # {"before": {...}, "after": {...}}


class ChatOut(BaseModel):
    reply: str
    change: ProposedChange | None = None


def chat(body: ChatIn) -> ChatOut:
    if settings.ai_mock:
        return ChatOut(
            reply="I moved the Valley of the Kings to the morning of day 2 so you avoid the midday heat.",
            change=ProposedChange(
                summary="Day 2: Valley of the Kings moved to 08:00",
                explanation="It is cooler and less crowded before 10:00.",
                cost_delta=0,
                diff={"before": {}, "after": {}},
            ),
        )
    # TODO(Person 3): call the LLM agent here.
    raise NotImplementedError


@router.post("/chat", response_model=ChatOut, summary="Chat agent (AI)")
def chat_route(body: ChatIn) -> ChatOut:
    return chat(body)
