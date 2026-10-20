"""Feature T7 · Hotels for travelers: filter list, details, and plain-language search."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pagination import Page, PageParams
from app.modules.accounts.models import User
from app.modules.ai_quality.service import search
from app.modules.hotels.models import Hotel
from app.modules.hotels.schemas import HotelCardOut, HotelSearchIn, HotelSearchOut
from app.modules.hotels.service import card_for, cards_query, to_card
from app.modules.trips.service import get_own_trip, trip_city_ids

router = APIRouter(prefix="/hotels", tags=["T7 · Hotels"])


@router.post("/search", response_model=HotelSearchOut)
def search_hotels(
    body: HotelSearchIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> HotelSearchOut:
    """AI. Why: travelers ask like people do: "4-star in Luxor under 1500 with free cancellation"
    (Arabic works too: "فندق 4 نجوم في الأقصر تحت 1500").
    How: app/ai/nl2sql.py writes a SELECT; we check it (only hotel_best_price and offers, read-only,
    3-second limit) and turn the hotel ids into hotel cards. Every search is logged in nl_queries
    for the admin AI-quality screen.
    If the AI fails: fallback=true with a message, so the screen shows the normal filters (GET /hotels).
    Then: open a hotel and compare its offers (GET /hotels/{id}/offers)."""
    city_id = body.city_id
    if body.trip_id is not None:
        trip = get_own_trip(db, user, body.trip_id)
        cities = trip_city_ids(db, trip.id)
        if city_id is None and len(cities) == 1:
            city_id = cities[0]
    log, cards, understood = search(db, user.id, body.question, city_id)
    if log.status == "failed":
        return HotelSearchOut(
            query_id=log.id,
            understood=None,
            results=[],
            count=0,
            fallback=True,
            message="Sorry, I couldn't run that search. Try the filters instead.",
        )
    return HotelSearchOut(
        query_id=log.id,
        understood=understood,
        results=cards,
        count=len(cards),
        fallback=False,
        message=None if cards else "No hotels match that yet. Try a higher price or fewer conditions.",
    )


@router.get("", response_model=Page[HotelCardOut])
def filter_hotels(
    city_id: int | None = None,
    stars: int | None = Query(None, ge=1, le=5, description="Exact star rating"),
    max_price: int | None = Query(None, ge=0, description="Lowest offer per night at most this (EGP)"),
    sort: str = Query("price", pattern="^(price|stars|name)$"),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
) -> Page[HotelCardOut]:
    """Why: normal filters work without AI, and they are the fallback when AI search fails. Public, no login.
    Each hotel shows its lowest active offer and how many companies sell it.
    With max_price, hotels without any active offer are left out (they have no price yet).
    Then: open one in GET /hotels/{id}, then compare its offers."""
    stmt, stats = cards_query()
    if city_id is not None:
        stmt = stmt.where(Hotel.city_id == city_id)
    if stars is not None:
        stmt = stmt.where(Hotel.stars == stars)
    if max_price is not None:
        stmt = stmt.where(stats.c.min_price <= max_price)
    order = {
        "price": [stats.c.min_price.asc().nulls_last(), Hotel.name],
        "stars": [Hotel.stars.desc().nulls_last(), Hotel.name],
        "name": [Hotel.name],
    }[sort]
    stmt = stmt.order_by(*order)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.execute(stmt.offset(params.offset).limit(params.limit)).all()
    return Page(data=[to_card(*r) for r in rows], page=params.page, limit=params.limit, total=int(total or 0))


@router.get("/{hotel_id}", response_model=HotelCardOut)
def hotel_detail(hotel_id: int, db: Session = Depends(get_db)) -> HotelCardOut:
    """Why: the traveler opens a hotel to see its details, lowest price and how many companies sell it.
    Public, no login.
    Then: the full list of competing offers is GET /hotels/{id}/offers (offers feature)."""
    return card_for(db, hotel_id)
