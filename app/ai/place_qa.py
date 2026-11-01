"""AI piece: "Ask more" about a place. Owner: Person 4.

Why: answers follow-up questions ONLY from the place's verified_info, so the AI doesn't invent history.
Then: the answer is shown under the scan result.

AI_MOCK=true: a simple grounded answer: the sentences of verified_info that share the most words with
the question. When no sentence matches, grounded=false and the answer says the notes don't cover it.
With USE_LLM=true the model answers from verified_info only (else grounded=false), and the matcher
above is the fallback when the model can't be reached.
"""

import json
import re

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

STOPWORDS = {
    "the", "a", "an", "is", "was", "were", "are", "of", "in", "on", "to", "and", "or", "it", "its", "this", "that",
    "what", "who", "when", "where", "why", "how", "did", "does", "do", "for", "with", "by", "from", "at", "as", "be",
    "about", "tell", "me", "can", "you", "there", "which", "much", "many",
}  # fmt: skip
NOT_COVERED = "Our verified notes about {name} don't cover that yet."


class AskIn(BaseModel):
    question: str
    place_name: str
    verified_info: str


class AskOut(BaseModel):
    answer: str
    grounded: bool  # False when the verified info doesn't contain the answer


def keywords(text: str) -> set[str]:
    words = {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 2}
    return words | {w[:-1] for w in words if w.endswith("s")}  # "pyramids" also matches "pyramid"


def grounded_answer(body: AskIn) -> AskOut:
    asked = keywords(body.question) - keywords(body.place_name)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.verified_info) if s.strip()]
    scored = sorted(((len(asked & keywords(s)), i, s) for i, s in enumerate(sentences)), key=lambda x: (-x[0], x[1]))
    best = [x for x in scored if x[0] > 0][:2]
    if not best:
        return AskOut(answer=NOT_COVERED.format(name=body.place_name), grounded=False)
    return AskOut(answer=" ".join(s for _, _, s in sorted(best, key=lambda x: x[1])), grounded=True)


QA_SYSTEM = """You answer travelers' questions about one place in Egypt.
Use ONLY the verified notes you are given. Never add facts from memory, even well-known ones.
If the notes don't answer the question, say so: set "grounded" to false.
Answer in the language of the question (English or Arabic), in 1-3 short sentences.
Reply with a JSON object only: {"answer": "...", "grounded": true}"""


def llm_answer(body: AskIn) -> AskOut:
    from app.ai.llm import LLMError, complete_json

    out = complete_json(
        QA_SYSTEM,
        json.dumps({"place": body.place_name, "verified_notes": body.verified_info, "question": body.question}),
        max_tokens=300,
    )
    answer, grounded = out.get("answer"), out.get("grounded")
    if not isinstance(answer, str) or not isinstance(grounded, bool):
        raise LLMError("the answer is missing")
    if not grounded or not answer.strip():
        return AskOut(answer=NOT_COVERED.format(name=body.place_name), grounded=False)
    return AskOut(answer=answer.strip(), grounded=True)


def ask(body: AskIn) -> AskOut:
    if settings.llm_ready:
        from app.ai.llm import LLMError

        try:
            return llm_answer(body)
        except LLMError:
            pass  # fall back to the sentence matcher below
    return grounded_answer(body)


@router.post("/ask", response_model=AskOut, summary="Place Q&A (AI)")
def ask_route(body: AskIn) -> AskOut:
    return ask(body)
