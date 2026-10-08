"""Place logic shared by the admin and traveler routes."""

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City
from app.modules.catalog.service import ensure_interests_exist, get_city_or_404
from app.modules.places.models import Place, PlaceImage, PlaceInterest
from app.modules.places.schemas import PlaceDetailOut, PlaceImageOut, PlaceOut


def get_place_or_404(db: Session, place_id: int) -> Place:
    place = db.get(Place, place_id)
    if place is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Place {place_id} not found")
    return place


def ensure_city_exists(db: Session, city_id: int) -> None:
    """A place must belong to a real city. Unknown city -> 400 (bad input), not 404 (missing URL)."""
    if db.get(City, city_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown city_id: {city_id}")


def ensure_label_free(db: Session, label: str | None, exclude_id: int | None = None) -> None:
    """Two places can't share a recognition label, or a scan wouldn't know which one it is."""
    if not label:
        return
    stmt = select(Place.id).where(Place.recognition_label == label)
    if exclude_id is not None:
        stmt = stmt.where(Place.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f'recognition_label "{label}" is already used by another place')


def set_interests(db: Session, place_id: int, interest_ids: list[int]) -> None:
    """Replaces the place's interests with exactly this list."""
    ensure_interests_exist(db, interest_ids)
    db.execute(delete(PlaceInterest).where(PlaceInterest.place_id == place_id))
    for interest_id in sorted(set(interest_ids)):
        db.add(PlaceInterest(place_id=place_id, interest_id=interest_id))


def interest_ids_by_place(db: Session, place_ids: list[int]) -> dict[int, list[int]]:
    """One query for many places, so a list of 20 places doesn't run 20 queries."""
    result: dict[int, list[int]] = {pid: [] for pid in place_ids}
    if not place_ids:
        return result
    rows = db.execute(
        select(PlaceInterest.place_id, PlaceInterest.interest_id)
        .where(PlaceInterest.place_id.in_(place_ids))
        .order_by(PlaceInterest.interest_id)
    )
    for place_id, interest_id in rows:
        result[place_id].append(interest_id)
    return result


def to_out(place: Place, interest_ids: list[int]) -> PlaceOut:
    columns = {c.key: getattr(place, c.key) for c in Place.__table__.columns}
    return PlaceOut.model_validate({**columns, "interest_ids": interest_ids})


def to_detail(db: Session, place: Place) -> PlaceDetailOut:
    city = get_city_or_404(db, place.city_id)
    images = db.scalars(select(PlaceImage).where(PlaceImage.place_id == place.id).order_by(PlaceImage.id))
    base = to_out(place, interest_ids_by_place(db, [place.id])[place.id])
    return PlaceDetailOut(
        **base.model_dump(),
        city_name=city.name,
        images=[PlaceImageOut.model_validate(img) for img in images],
    )
