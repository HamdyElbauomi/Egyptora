"""Features A4 (places part) and A5 (scans part) · Places, images, scan review (admin)."""

import shutil

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.core.pagination import Page, PageParams, paginate
from app.core.storage import delete_file, save_image, upload_root
from app.modules.accounts.models import User
from app.modules.places.models import PLACE_TYPES, Place, PlaceImage
from app.modules.places.schemas import LabelScanIn, PlaceImageOut, PlaceIn, PlaceOut, PlaceUpdateIn
from app.modules.places.service import (
    ensure_city_exists,
    ensure_label_free,
    get_place_or_404,
    interest_ids_by_place,
    set_interests,
    to_out,
)

router = APIRouter(prefix="/admin", tags=["A4-A5 · Admin places and scans"])
admin = require_role("admin")
MAX_IMAGES_PER_UPLOAD = 10


@router.get("/places", response_model=Page[PlaceOut])
def list_places(
    city_id: int | None = None,
    type: str | None = Query(None, pattern=f"^({'|'.join(PLACE_TYPES)})$"),
    search: str | None = Query(None, description="Part of the place name, any case"),
    params: PageParams = Depends(),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> Page[PlaceOut]:
    """Why: the admin manages the list of places trips are built from. Filter by city, type or name."""
    stmt = select(Place).order_by(Place.city_id, Place.id)
    if city_id is not None:
        stmt = stmt.where(Place.city_id == city_id)
    if type is not None:
        stmt = stmt.where(Place.type == type)
    if search:
        stmt = stmt.where(func.lower(Place.name).contains(search.lower()))
    places, total = paginate(db, stmt, params)
    interests = interest_ids_by_place(db, [p.id for p in places])
    return Page(data=[to_out(p, interests[p.id]) for p in places], page=params.page, limit=params.limit, total=total)


@router.post("/places", response_model=PlaceOut, status_code=201)
def add_place(body: PlaceIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> PlaceOut:
    """Why: add a place with verified info, a source link and its interests.
    Then: the trip planner can put it in trips, and the camera can recognize it if it has a recognition_label."""
    ensure_city_exists(db, body.city_id)
    ensure_label_free(db, body.recognition_label)
    place = Place(**body.model_dump(exclude={"interest_ids"}))
    db.add(place)
    db.flush()  # gives the place its id before we link interests
    set_interests(db, place.id, body.interest_ids)
    db.commit()
    db.refresh(place)
    return to_out(place, sorted(set(body.interest_ids)))


@router.patch("/places/{place_id}", response_model=PlaceOut)
def update_place(
    place_id: int, body: PlaceUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> PlaceOut:
    """Why: fix wrong history, hours or ticket price. Only the fields you send are changed;
    interest_ids, when sent, replaces the whole list.
    Then: the camera and trips show the corrected info."""
    place = get_place_or_404(db, place_id)
    changes = body.model_dump(exclude_unset=True)
    interest_ids = changes.pop("interest_ids", None)
    if changes.get("city_id") is not None:
        ensure_city_exists(db, changes["city_id"])
    if "recognition_label" in changes:
        ensure_label_free(db, changes["recognition_label"], exclude_id=place_id)
    for field, value in changes.items():
        if field in {"city_id", "name", "type"} and value is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{field} can't be empty")
        setattr(place, field, value)
    if interest_ids is not None:
        set_interests(db, place_id, interest_ids)
    db.commit()
    db.refresh(place)
    return to_out(place, interest_ids_by_place(db, [place_id])[place_id])


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> None:
    """Why: remove a closed or duplicate place.
    Effect: its images are deleted too; trip items and scans that used it keep existing with place_id = null."""
    place = get_place_or_404(db, place_id)
    db.delete(place)
    db.commit()
    shutil.rmtree(upload_root() / "places" / str(place_id), ignore_errors=True)


@router.post("/places/{place_id}/images", response_model=list[PlaceImageOut], status_code=201)
async def upload_place_images(
    place_id: int,
    files: list[UploadFile] = File(..., description="JPEG, PNG or WebP, up to 5 MB each, max 10 per upload"),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> list[PlaceImage]:
    """Why: the vision model needs labeled photos of each monument to learn it.
    Then: these images are used to train and test app/ai/recognizer.py."""
    get_place_or_404(db, place_id)
    if len(files) > MAX_IMAGES_PER_UPLOAD:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Upload at most {MAX_IMAGES_PER_UPLOAD} images at once")
    saved: list[str] = []
    try:
        for file in files:
            saved.append(await save_image(file, f"places/{place_id}"))
    except HTTPException:
        for url in saved:  # one bad file -> nothing is kept, so the upload is all or nothing
            delete_file(url)
        raise
    images = [PlaceImage(place_id=place_id, image_url=url, source="admin") for url in saved]
    db.add_all(images)
    db.commit()
    for image in images:
        db.refresh(image)
    return images


@router.delete("/place-images/{image_id}", status_code=204)
def delete_place_image(image_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> None:
    """Why: remove blurry or wrong photos that confuse the model. Deletes the file too."""
    image = db.get(PlaceImage, image_id)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Image {image_id} not found")
    url = image.image_url
    db.delete(image)
    db.commit()
    delete_file(url)


@router.get("/ai/scans")
def low_confidence_scans(max_confidence: float = 0.6, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin sees scans the model was unsure about.
    Then: labels them in POST /admin/ai/scans/{id}/label. (Built with the camera feature.)"""
    raise not_implemented("Person 4")


@router.post("/ai/scans/{scan_id}/label")
def label_scan(scan_id: int, body: LabelScanIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: correct the model's mistake by choosing the right place.
    Then: the photo can be added to place_images, so the next training run improves. (Built with the camera feature.)"""
    raise not_implemented("Person 4")
