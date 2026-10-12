"""Hotel logic shared by the admin and traveler routes."""

import csv
import io

from fastapi import HTTPException, status
from sqlalchemy import Select, Subquery, func, select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City
from app.modules.hotels.models import Hotel
from app.modules.hotels.schemas import HotelCardOut, HotelIn, ImportRowError
from app.modules.offers.models import Offer

CSV_COLUMNS = ["city", "name", "stars", "address", "lat", "lng", "description", "amenities", "image_url"]


def get_hotel_or_404(db: Session, hotel_id: int) -> Hotel:
    hotel = db.get(Hotel, hotel_id)
    if hotel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hotel {hotel_id} not found")
    return hotel


def ensure_city_exists(db: Session, city_id: int) -> None:
    if db.get(City, city_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown city_id: {city_id}")


def ensure_unique_in_city(db: Session, city_id: int, name: str, exclude_id: int | None = None) -> None:
    """Two hotels with the same name in the same city would confuse companies and travelers."""
    stmt = select(Hotel.id).where(Hotel.city_id == city_id, func.lower(Hotel.name) == name.strip().lower())
    if exclude_id is not None:
        stmt = stmt.where(Hotel.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f'"{name}" already exists in this city')


def active_offers_count(db: Session, hotel_id: int) -> int:
    return int(db.scalar(select(func.count(Offer.id)).where(Offer.hotel_id == hotel_id, Offer.status == "active")) or 0)


def cards_query() -> tuple[Select, Subquery]:
    """Hotels joined with their city name and live offer stats (lowest active price, number of active offers)."""
    stats = (
        select(
            Offer.hotel_id,
            func.min(Offer.price_per_night).label("min_price"),
            func.count(Offer.id).label("offers_count"),
        )
        .where(Offer.status == "active")
        .group_by(Offer.hotel_id)
        .subquery()
    )
    return (
        select(Hotel, City.name, stats.c.min_price, func.coalesce(stats.c.offers_count, 0))
        .join(City, City.id == Hotel.city_id)
        .outerjoin(stats, stats.c.hotel_id == Hotel.id)
    ), stats


def to_card(hotel: Hotel, city_name: str, min_price: int | None, offers_count: int) -> HotelCardOut:
    columns = {c.key: getattr(hotel, c.key) for c in Hotel.__table__.columns}
    columns["amenities"] = columns.get("amenities") or []
    return HotelCardOut(**columns, city_name=city_name, min_price=min_price, offers_count=offers_count)


def card_for(db: Session, hotel_id: int) -> HotelCardOut:
    stmt, _ = cards_query()
    row = db.execute(stmt.where(Hotel.id == hotel_id)).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hotel {hotel_id} not found")
    return to_card(*row)


def parse_csv(db: Session, raw: bytes) -> tuple[list[HotelIn], list[ImportRowError]]:
    """Reads the import file. Columns: city (name), name, stars, address, lat, lng, description,
    amenities (separated by ;), image_url. Only city and name are required.
    Returns the valid rows and every error found, so the admin can fix the whole file at once."""
    try:
        text = raw.decode("utf-8-sig")  # utf-8-sig also reads files saved by Excel
    except UnicodeDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file must be a UTF-8 CSV") from exc
    reader = csv.DictReader(io.StringIO(text))
    missing = {"city", "name"} - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Missing required columns: {sorted(missing)}")

    cities = {name.lower(): cid for cid, name in db.execute(select(City.id, City.name))}
    rows: list[HotelIn] = []
    errors: list[ImportRowError] = []
    for line, record in enumerate(reader, start=2):
        city_id = cities.get((record.get("city") or "").strip().lower())
        if city_id is None:
            errors.append(ImportRowError(row=line, error=f'Unknown city "{record.get("city")}"'))
            continue
        try:
            rows.append(
                HotelIn(
                    city_id=city_id,
                    name=(record.get("name") or "").strip(),
                    stars=int(record["stars"]) if record.get("stars") else None,
                    address=record.get("address") or None,
                    lat=float(record["lat"]) if record.get("lat") else None,
                    lng=float(record["lng"]) if record.get("lng") else None,
                    description=record.get("description") or None,
                    amenities=[a.strip() for a in (record.get("amenities") or "").split(";") if a.strip()],
                    image_url=record.get("image_url") or None,
                )
            )
        except ValueError as exc:  # also catches pydantic's ValidationError
            first = str(exc).splitlines()
            errors.append(ImportRowError(row=line, error=" ".join(first[:3])))
    return rows, errors
