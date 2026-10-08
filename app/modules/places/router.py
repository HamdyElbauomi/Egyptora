"""Feature T6 · Scan a monument (traveler side). Owner: Person 4."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.places.schemas import AskIn, PlaceDetailOut
from app.modules.places.service import get_place_or_404, to_detail

router = APIRouter(tags=["T6 · Scan a monument"])
OWNER = "Person 4"
traveler = require_role("traveler")


@router.post("/scans", status_code=201)
async def scan(photo: UploadFile, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """AI. Why: the traveler points the camera at a monument and wants to know what it is.
    Then: calls app/ai/recognizer.py, finds the place by recognition_label, returns verified_info,
    logs the scan. Under settings.scan_confidence_threshold return place=null ("not sure")."""
    raise not_implemented(OWNER)


@router.get("/scans")
def my_scans(user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: the traveler wants to see monuments they scanned before.
    Then: opens the place in GET /places/{id}."""
    raise not_implemented(OWNER)


@router.get("/places/{place_id}", response_model=PlaceDetailOut, tags=["Places"])
def place_detail(place_id: int, db: Session = Depends(get_db)) -> PlaceDetailOut:
    """Why: full place details (with city name and photos) for the scan result and for trip items.
    Public: no login needed.
    Then: "Add to trip" calls POST /trips/{id}/days/{dayId}/items with this place_id."""
    return to_detail(db, get_place_or_404(db, place_id))


@router.post("/places/{place_id}/ask")
def ask_about_place(place_id: int, body: AskIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """AI. Why: the traveler wants to know more ("who built it?", "best time to visit?").
    Then: calls app/ai/place_qa.py with this place's verified_info only."""
    raise not_implemented(OWNER)
