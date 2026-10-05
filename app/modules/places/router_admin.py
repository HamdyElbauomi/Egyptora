"""Features A4 (places part) and A5 (scans part) · Places, images, scan review. Owner: Person 4."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.places.schemas import LabelScanIn, PlaceIn, PlaceUpdateIn

router = APIRouter(prefix="/admin", tags=["A4-A5 · Admin places and scans"])
OWNER = "Person 4"
admin = require_role("admin")


@router.get("/places")
def list_places(
    city_id: int | None = None, type: str | None = None, user: User = Depends(admin), db: Session = Depends(get_db)
):
    """Why: the admin manages the list of places trips are built from."""
    raise not_implemented(OWNER)


@router.post("/places", status_code=201)
def add_place(body: PlaceIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: add a place with verified info, a source link and its interests.
    Then: Person 2's planner can now put it in trips."""
    raise not_implemented(OWNER)


@router.patch("/places/{place_id}")
def update_place(place_id: int, body: PlaceUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: fix wrong history, hours or ticket price.
    Then: the camera and trips show the corrected info."""
    raise not_implemented(OWNER)


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: remove a closed or duplicate place."""
    raise not_implemented(OWNER)


@router.post("/places/{place_id}/images", status_code=201)
async def upload_place_images(
    place_id: int, files: list[UploadFile], user: User = Depends(admin), db: Session = Depends(get_db)
):
    """Why: the vision model needs labeled photos of each monument to learn it.
    Then: images feed training of app/ai/recognizer.py."""
    raise not_implemented(OWNER)


@router.delete("/place-images/{image_id}", status_code=204)
def delete_place_image(image_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: remove blurry or wrong photos that confuse the model."""
    raise not_implemented(OWNER)


@router.get("/ai/scans")
def low_confidence_scans(max_confidence: float = 0.6, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin sees scans the model was unsure about.
    Then: labels them in POST /admin/ai/scans/{id}/label."""
    raise not_implemented(OWNER)


@router.post("/ai/scans/{scan_id}/label")
def label_scan(scan_id: int, body: LabelScanIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: correct the model's mistake by choosing the right place.
    Then: the photo can be added to place_images, so the next training run improves."""
    raise not_implemented(OWNER)
