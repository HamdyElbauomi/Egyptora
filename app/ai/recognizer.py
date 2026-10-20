"""AI piece: monument recognition. Owner: Person 4.

Why: turns a photo into a place label and a confidence.
Then: POST /scans finds the place whose recognition_label matches and returns its verified_info.
Below settings.scan_confidence_threshold the app says "not sure" and the admin reviews the scan.

AI_MOCK=true: every photo is "karnak_temple" with confidence 0.91, unless the file contains the text
`egyptora-mock:<label>:<confidence>` (tests use this to try other labels and the "not sure" path).
"""

import re

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

MOCK_MARKER = re.compile(rb"egyptora-mock:([a-z0-9_]*):([0-9.]+)")


class RecognizeOut(BaseModel):
    label: str | None  # a places.recognition_label, or None when the model sees no known monument
    confidence: float  # 0..1


def recognize(image_bytes: bytes) -> RecognizeOut:
    if settings.ai_mock:
        match = MOCK_MARKER.search(image_bytes)
        if match:
            return RecognizeOut(label=match.group(1).decode() or None, confidence=float(match.group(2)))
        return RecognizeOut(label="karnak_temple", confidence=0.91)
    # TODO(Person 4): run the vision model here (trained on place_images where used_for_training is true).
    raise NotImplementedError


@router.post("/recognize", response_model=RecognizeOut, summary="Monument recognition (AI)")
async def recognize_route(photo: UploadFile) -> RecognizeOut:
    return recognize(await photo.read())
