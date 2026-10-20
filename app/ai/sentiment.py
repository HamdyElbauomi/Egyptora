"""AI piece: review sentiment. Owner: Person 1.

Why: turns review text into positive / neutral / negative plus the top complaints.
Then: used by company review insights, admin "analyze reviews", and every new traveler review.

AI_MOCK=true uses a word list (English and Egyptian Arabic): good words push the score up, bad words down,
"not"/"مش" flips the next word. Complaints are topics (pickup delays, cleanliness...) found in
negative or neutral reviews, most frequent first. The real model must return the same SentimentOut.
"""

import re
from collections import Counter

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

POSITIVE = {
    "great", "good", "excellent", "amazing", "perfect", "friendly", "helpful", "clean", "comfortable", "recommend",
    "wonderful", "love", "loved", "nice", "fantastic", "professional", "smooth", "best", "punctual", "on time",
    "ممتاز", "ممتازة", "جميل", "جميلة", "حلو", "حلوة", "رائع", "رائعة", "نضيف", "نظيف", "محترم", "محترمين", "انصح",
    "أنصح", "تحفة", "مريح",
}  # fmt: skip
NEGATIVE = {
    "bad", "terrible", "awful", "late", "delay", "delayed", "dirty", "rude", "worst", "poor", "noisy", "smaller",
    "small", "expensive", "overpriced", "cancelled", "canceled", "scam", "disappointed", "disappointing", "broken",
    "never", "slow", "unhelpful", "problem", "وحش", "وحشة", "زبالة", "متأخر", "اتأخر", "اتأخروا", "تأخير", "وسخ",
    "مش نضيف", "غالي", "نصب", "سيء", "سيئ", "مشكلة", "مقرف", "قليل الذوق",
}  # fmt: skip
NEGATORS = {"not", "no", "never", "isn't", "wasn't", "didn't", "مش", "مكانش", "ماكانش"}

COMPLAINTS = {
    "late pickup or delays": ("late", "delay", "delayed", "waited", "متأخر", "اتأخر", "اتأخروا", "تأخير", "استنينا"),
    "cleanliness": ("dirty", "clean", "وسخ", "نضيف", "نظيف"),
    "room smaller than photos": ("small", "smaller", "photos", "صغيرة", "الصور"),
    "staff attitude": ("rude", "unhelpful", "staff", "guide", "قليل الذوق", "المرشد", "الموظف"),
    "price or hidden fees": ("expensive", "overpriced", "fees", "price", "charged", "غالي", "فلوس", "السعر"),
    "cancellation or refund": ("cancel", "cancelled", "canceled", "refund", "الغاء", "إلغاء", "استرجاع"),
    "noise": ("noisy", "noise", "دوشة", "دوشه"),
}


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


def score_text(text: str) -> float:
    t = text.lower()
    tokens = re.findall(r"[\w']+", t)
    points = 0
    for i, token in enumerate(tokens):
        sign = -1 if i > 0 and tokens[i - 1] in NEGATORS else 1
        if token in POSITIVE:
            points += sign
        elif token in NEGATIVE:
            points -= sign
    for phrase in [p for p in NEGATIVE | POSITIVE if " " in p]:  # multi-word phrases
        if phrase in t:
            points += 1 if phrase in POSITIVE else -1
    if points == 0:
        return 0.0
    return max(-1.0, min(1.0, points / 3))


def label(score: float) -> str:
    return "positive" if score >= 0.25 else "negative" if score <= -0.25 else "neutral"


def complaints_of(texts: list[str], limit: int = 3) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        t = text.lower()
        for topic, words in COMPLAINTS.items():
            if any(w in t for w in words):
                counts[topic] += 1
    return [topic for topic, _ in counts.most_common(limit)]


def rules_analyze(reviews: list[str]) -> SentimentOut:
    items = [ReviewSentiment(text=r, sentiment=label(s), score=round(s, 3)) for r in reviews for s in [score_text(r)]]
    positive = sum(1 for i in items if i.sentiment == "positive")
    unhappy = [i.text for i in items if i.sentiment != "positive"]
    return SentimentOut(
        items=items,
        positive_share=round(positive / len(items), 3) if items else 0.0,
        top_complaints=complaints_of(unhappy),
    )


def analyze(reviews: list[str]) -> SentimentOut:
    if settings.ai_mock:
        return rules_analyze(reviews)
    # TODO(Person 1): call the real model here.
    raise NotImplementedError


@router.post("/sentiment", response_model=SentimentOut, summary="Review sentiment (AI)")
def sentiment_route(body: SentimentIn) -> SentimentOut:
    return analyze(body.reviews)
