"""Feature A3 (hotels part) · Admin hotels."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams
from app.modules.accounts.models import User
from app.modules.hotels.models import Hotel
from app.modules.hotels.schemas import HotelCardOut, HotelIn, HotelUpdateIn, ImportOut
from app.modules.hotels.service import (
    active_offers_count,
    card_for,
    cards_query,
    ensure_city_exists,
    ensure_unique_in_city,
    get_hotel_or_404,
    parse_csv,
    to_card,
)

router = APIRouter(prefix="/admin/hotels", tags=["A3 · Admin hotels"])
admin = require_role("admin")
MAX_CSV_BYTES = 2 * 1024 * 1024


@router.get("", response_model=Page[HotelCardOut])
def list_hotels(
    city_id: int | None = None,
    search: str | None = Query(None, description="Part of the hotel name, any case"),
    params: PageParams = Depends(),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> Page[HotelCardOut]:
    """Why: the admin sees every hotel with how many active offers it has and its lowest price."""
    stmt, _ = cards_query()
    stmt = stmt.order_by(Hotel.city_id, Hotel.name)
    if city_id is not None:
        stmt = stmt.where(Hotel.city_id == city_id)
    if search:
        stmt = stmt.where(func.lower(Hotel.name).contains(search.lower()))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.execute(stmt.offset(params.offset).limit(params.limit)).all()
    return Page(data=[to_card(*r) for r in rows], page=params.page, limit=params.limit, total=int(total or 0))


@router.post("", response_model=HotelCardOut, status_code=201)
def add_hotel(body: HotelIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> HotelCardOut:
    """Why: companies can only sell hotels that exist, so the admin adds them first.
    Then: companies can attach offers to it."""
    ensure_city_exists(db, body.city_id)
    ensure_unique_in_city(db, body.city_id, body.name)
    hotel = Hotel(**body.model_dump())
    hotel.name = body.name.strip()
    db.add(hotel)
    db.commit()
    return card_for(db, hotel.id)


@router.patch("/{hotel_id}", response_model=HotelCardOut)
def update_hotel(
    hotel_id: int, body: HotelUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> HotelCardOut:
    """Why: fix name, stars, location or amenities. Only the fields you send are changed."""
    hotel = get_hotel_or_404(db, hotel_id)
    changes = body.model_dump(exclude_unset=True)
    for field in ("city_id", "name"):
        if field in changes and changes[field] is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{field} can't be empty")
    if "city_id" in changes:
        ensure_city_exists(db, changes["city_id"])
    if "name" in changes or "city_id" in changes:
        ensure_unique_in_city(
            db, changes.get("city_id", hotel.city_id), changes.get("name", hotel.name), exclude_id=hotel_id
        )
    for field, value in changes.items():
        setattr(hotel, field, value.strip() if field == "name" else value)
    db.commit()
    return card_for(db, hotel_id)


@router.delete("/{hotel_id}", status_code=204)
def delete_hotel(hotel_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> None:
    """Why: remove a closed or duplicate hotel.
    Blocked (409) while companies still have active offers on it: pause or delete those first."""
    hotel = get_hotel_or_404(db, hotel_id)
    active = active_offers_count(db, hotel_id)
    if active:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Hotel has {active} active offers; they must be paused first")
    db.delete(hotel)
    db.commit()


@router.post("/import", response_model=ImportOut, status_code=201)
async def import_hotels(
    file: UploadFile = File(
        ...,
        description="CSV with columns: city, name, stars, address, lat, lng, "
        "description, amenities (separated by ;), image_url",
    ),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> ImportOut:
    """Why: typing 30-50 hotels by hand is slow. Only `city` (a city name) and `name` are required.
    All or nothing: if any row has an error, nothing is imported and every error is listed (400).
    Hotels that already exist (same name in the same city) are skipped, so re-uploading the file is safe."""
    raw = await file.read()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV is larger than 2 MB")
    rows, errors = parse_csv(db, raw)
    if errors:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {
                "message": f"{len(errors)} rows have errors; nothing was imported",
                "errors": [e.model_dump() for e in errors],
            },
        )
    existing = {(cid, name.lower()) for cid, name in db.execute(select(Hotel.city_id, Hotel.name))}
    created, skipped = 0, []
    for row in rows:
        key = (row.city_id, row.name.lower())
        if key in existing:
            skipped.append(row.name)
            continue
        db.add(Hotel(**row.model_dump()))
        existing.add(key)
        created += 1
    db.commit()
    return ImportOut(created=created, skipped=len(skipped), skipped_names=skipped)
