"""Catalog logic shared by the admin routes and the preference lookups."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City, Interest


def get_city_or_404(db: Session, city_id: int) -> City:
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"City {city_id} not found")
    return city


def get_interest_or_404(db: Session, interest_id: int) -> Interest:
    interest = db.get(Interest, interest_id)
    if interest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Interest {interest_id} not found")
    return interest


def ensure_unique_name(db: Session, model: type[City] | type[Interest], name: str, exclude_id: int | None = None):
    """Names are unique ignoring case ("Luxor" and "luxor" clash). Raises 409 on a clash."""
    stmt = select(model.id).where(func.lower(model.name) == name.strip().lower())
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f'"{name}" already exists')


def ensure_interests_exist(db: Session, interest_ids: list[int]) -> None:
    """Raises 400 listing any interest ids that don't exist."""
    if not interest_ids:
        return
    found = set(db.scalars(select(Interest.id).where(Interest.id.in_(interest_ids))))
    missing = sorted(set(interest_ids) - found)
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown interest ids: {missing}")


def recommended_city_count(days: int) -> int:
    """Short trips stay in one city; longer trips can cover more without rushing."""
    if days <= 3:
        return 1
    if days <= 6:
        return 2
    return 3
