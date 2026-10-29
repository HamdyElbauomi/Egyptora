"""Feature T2 · Preferences lookups (public, no login needed)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.catalog.models import City, Interest
from app.modules.catalog.schemas import CityCardOut, CityOut, CitySuggestion, InterestOut, SuggestOut
from app.modules.catalog.service import ensure_interests_exist, recommended_city_count
from app.modules.places.models import Place
from app.modules.places.schemas import PlaceOut
from app.modules.places.service import interest_ids_by_place, to_out
from app.modules.trips.service import rank_cities_by_interests

router = APIRouter(tags=["T2 · Preferences"])


@router.get("/interests", response_model=list[InterestOut])
def list_interests(db: Session = Depends(get_db)) -> list[Interest]:
    """Why: preference step 1 needs the list of interest chips.
    Then: the chosen interest ids go into POST /trips/generate."""
    return list(db.scalars(select(Interest).order_by(Interest.id)))


@router.get("/cities", response_model=list[CityCardOut])
def list_cities(db: Session = Depends(get_db)) -> list[CityCardOut]:
    """Why: preference step 4 needs the destination cards, each with how many places it has.
    Then: the chosen city ids go into POST /trips/generate."""
    places_count = select(Place.city_id, func.count(Place.id).label("n")).group_by(Place.city_id).subquery()
    rows = db.execute(
        select(City, func.coalesce(places_count.c.n, 0))
        .outerjoin(places_count, places_count.c.city_id == City.id)
        .order_by(City.id)
    ).all()
    return [CityCardOut(**CityOut.model_validate(city).model_dump(), places_count=n) for city, n in rows]


@router.get("/cities/suggest", response_model=SuggestOut)
def suggest_cities(
    interests: list[int] = Query(
        default=[], description="Interest ids chosen in step 1. Repeat the key: ?interests=1&interests=3"
    ),
    days: int = Query(3, ge=1, le=21, description="Trip length chosen in step 3"),
    budget: str = Query("mid", pattern="^(low|mid|high)$", description="Not used for ranking yet"),
    db: Session = Depends(get_db),
) -> SuggestOut:
    """Why: some travelers don't know where to go and tap "suggest for me".
    How: every city is ranked by how many of its places match the chosen interests;
    the trip length decides how many cities to pre-select (1-3 days: 1, 4-6 days: 2, 7+: 3).
    Then: the front end pre-selects the cities with selected=true before POST /trips/generate."""
    ensure_interests_exist(db, interests)
    rows = rank_cities_by_interests(db, interests)

    count = min(recommended_city_count(days), len(rows))
    suggestions = [
        CitySuggestion(city=CityOut.model_validate(city), matching_places=n, selected=i < count and n > 0)
        for i, (city, n) in enumerate(rows)
    ]
    return SuggestOut(recommended_count=count, suggestions=suggestions)


@router.get("/cities/{city_id}/places", response_model=list[PlaceOut])
def list_city_places(city_id: int, db: Session = Depends(get_db)) -> list[PlaceOut]:
    """Why: the trip page's "Add a place" lists what can be added to a day in that city.
    Then: the chosen place id goes into POST /trips/{trip_id}/days/{day_id}/items."""
    if db.get(City, city_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "City not found")
    places = list(db.scalars(select(Place).where(Place.city_id == city_id).order_by(Place.name)))
    interests = interest_ids_by_place(db, [p.id for p in places])
    return [to_out(p, interests[p.id]) for p in places]
