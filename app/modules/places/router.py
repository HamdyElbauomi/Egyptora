"""Feature T6 · Scan a monument (traveler side). Owner: Person 4."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.place_qa import AskIn as QaIn
from app.ai.place_qa import ask
from app.ai.recognizer import recognize
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate_rows
from app.core.storage import save_image
from app.modules.accounts.models import User
from app.modules.places.models import Place, Scan
from app.modules.places.schemas import AnswerOut, AskIn, PlaceDetailOut, ScanListItem, ScanOut
from app.modules.places.service import get_place_or_404, scans_query, to_detail

router = APIRouter(tags=["T6 · Scan a monument"])
traveler = require_role("traveler")


@router.post("/scans", status_code=201, response_model=ScanOut)
async def scan(
    photo: UploadFile = File(..., description="JPEG, PNG or WebP, up to 5 MB"),
    user: User = Depends(traveler),
    db: Session = Depends(get_db),
) -> ScanOut:
    """AI. Why: the traveler points the camera at a monument and wants to know what it is.
    How: the photo is saved, the recognizer (app/ai/recognizer.py) returns a label and a confidence,
    and the label is matched to a place's recognition_label.
    At or above settings.scan_confidence_threshold (0.6): status="recognized" with the full place
    (verified_info, photos). Below it, or for an unknown label: status="not_sure", place=null,
    and the scan waits in the admin review queue (GET /admin/ai/scans).
    Then: "Ask more" (POST /places/{id}/ask) or "Add to trip" (POST /trips/{id}/days/{dayId}/items)."""
    content = await photo.read()
    await photo.seek(0)
    image_url = await save_image(photo, f"scans/{user.id}")
    result = recognize(content)

    place = None
    if result.label and result.confidence >= settings.scan_confidence_threshold:
        place = db.scalar(select(Place).where(Place.recognition_label == result.label))
    record = Scan(
        user_id=user.id, image_url=image_url, place_id=place.id if place else None, confidence=result.confidence
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if place is None:
        return ScanOut(
            scan_id=record.id,
            status="not_sure",
            confidence=result.confidence,
            image_url=image_url,
            place=None,
            message="We're not sure which monument this is. Try another angle, closer and in good light.",
        )
    return ScanOut(
        scan_id=record.id,
        status="recognized",
        confidence=result.confidence,
        image_url=image_url,
        place=to_detail(db, place),
        message=f"This is {place.name}.",
    )


@router.get("/scans", response_model=Page[ScanListItem])
def my_scans(
    params: PageParams = Depends(), user: User = Depends(traveler), db: Session = Depends(get_db)
) -> Page[ScanListItem]:
    """Why: the traveler wants to see monuments they scanned before, newest first.
    place_id is null for scans we weren't sure about (it fills in if an admin labels the photo later).
    Then: opens the place in GET /places/{id}."""
    stmt = scans_query().where(Scan.user_id == user.id).order_by(Scan.created_at.desc(), Scan.id.desc())
    rows, total = paginate_rows(db, stmt, params)
    return Page(
        data=[to_list_item(s, place_name, city_name) for s, place_name, city_name in rows],
        page=params.page,
        limit=params.limit,
        total=total,
    )


def to_list_item(s: Scan, place_name: str | None, city_name: str | None) -> ScanListItem:
    return ScanListItem(
        id=s.id,
        image_url=s.image_url,
        confidence=float(s.confidence) if s.confidence is not None else None,
        place_id=s.place_id,
        place_name=place_name,
        city_name=city_name,
        created_at=s.created_at,
    )


@router.get("/places/{place_id}", response_model=PlaceDetailOut, tags=["Places"])
def place_detail(place_id: int, db: Session = Depends(get_db)) -> PlaceDetailOut:
    """Why: full place details (with city name and photos) for the scan result and for trip items.
    Public: no login needed. Photos from travelers' scans are not shown here.
    Then: "Add to trip" calls POST /trips/{id}/days/{dayId}/items with this place_id."""
    return to_detail(db, get_place_or_404(db, place_id))


@router.post("/places/{place_id}/ask", response_model=AnswerOut)
def ask_about_place(
    place_id: int, body: AskIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> AnswerOut:
    """AI. Why: the traveler wants to know more ("who built it?", "when was it built?").
    The answer comes ONLY from this place's checked verified_info (app/ai/place_qa.py).
    grounded=false means the notes don't answer it, so nothing is made up.
    409 when the place has no verified info yet."""
    place = get_place_or_404(db, place_id)
    if not place.verified_info:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{place.name} has no verified info yet")
    out = ask(QaIn(question=body.question, place_name=place.name, verified_info=place.verified_info))
    return AnswerOut(answer=out.answer, grounded=out.grounded, source_url=place.source_url if out.grounded else None)
