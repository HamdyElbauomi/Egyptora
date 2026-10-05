"""AI piece: "Ask more" about a place. Owner: Person 4.

Why: answers follow-up questions ONLY from the place's verified_info, so the AI doesn't invent history.
Then: the answer is shown under the scan result.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])


class AskIn(BaseModel):
    question: str
    place_name: str
    verified_info: str


class AskOut(BaseModel):
    answer: str
    grounded: bool  # False when the verified info doesn't contain the answer


def ask(body: AskIn) -> AskOut:
    if settings.ai_mock:
        return AskOut(answer=f"According to our verified notes on {body.place_name}: ...", grounded=True)
    # TODO(Person 4): call the LLM with verified_info as the only context.
    raise NotImplementedError


@router.post("/ask", response_model=AskOut, summary="Place Q&A (AI)")
def ask_route(body: AskIn) -> AskOut:
    return ask(body)
