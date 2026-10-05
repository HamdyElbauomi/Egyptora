"""AI piece: review sentiment. Owner: Person 1.

Why: turns review text into positive / neutral / negative plus the top complaints.
Then: used by company review insights, admin "analyze reviews", and every new traveler review.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])


class SentimentIn(BaseModel):
    reviews: list[str]


class ReviewSentiment(BaseModel):
    text: str
    sentiment: str  # positive | neutral | negative
    score: float  # -1.0 .. 1.0


class SentimentOut(BaseModel):
    items: list[ReviewSentiment]
    positive_share: float  # 0..1
    top_complaints: list[str]


def analyze(reviews: list[str]) -> SentimentOut:
    if settings.ai_mock:
        items = [ReviewSentiment(text=r, sentiment="positive", score=0.8) for r in reviews]
        return SentimentOut(
            items=items, positive_share=0.82, top_complaints=["late pickup", "room smaller than photos"]
        )
    # TODO(Person 1): call the real model here.
    raise NotImplementedError


@router.post("/sentiment", response_model=SentimentOut, summary="Review sentiment (AI)")
def sentiment_route(body: SentimentIn) -> SentimentOut:
    return analyze(body.reviews)
