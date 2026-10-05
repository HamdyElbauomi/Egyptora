"""AI piece: monument recognition. Owner: Person 4.

Why: turns a photo into a place label and a confidence.
Then: POST /scans finds the place whose recognition_label matches and returns its verified_info.
Below settings.scan_confidence_threshold the app says "not sure" and the admin reviews the scan.
"""

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])


class RecognizeOut(BaseModel):
    label: str | None
    confidence: float


def recognize(image_bytes: bytes) -> RecognizeOut:
    if settings.ai_mock:
        return RecognizeOut(label="karnak_temple", confidence=0.91)
    # TODO(Person 4): run the vision model here.
    raise NotImplementedError


@router.post("/recognize", response_model=RecognizeOut, summary="Monument recognition (AI)")
async def recognize_route(photo: UploadFile) -> RecognizeOut:
    return recognize(await photo.read())
