"""Trip logic: build a trip, load it for the screens, and the checks every trip endpoint shares. Owner: Person 2.

generate_trip() steps:
1. Resolve cities (body.city_ids, or the suggestion ranking when body.suggest is true).
2. Collect candidate places for those cities, each with its interest ids.
3. Collect the best offers per city (offers/service.py -> best_offers_for_cities).
4. Call app/ai/planner.py -> plan_trip().
5. Save trips, trip_interests, trip_cities, trip_days, trip_items.
6. recalculate_total() from totals.py.
"""

from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai.planner import CandidateOffer, CandidatePlace, PlanIn, PlanOut, plan_trip
from app.modules.accounts.models import User
from app.modules.catalog.models import City
from app.modules.catalog.service import ensure_interests_exist, recommended_city_count
from app.modules.companies.models import Company
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer
from app.modules.offers.service import best_offers_for_cities
from app.modules.places.models import Place, PlaceInterest
from app.modules.trips.models import Trip, TripCity, TripDay, TripInterest, TripItem
from app.modules.trips.schemas import (
    DayHotelOut,
    GenerateTripIn,
    TripCardOut,
    TripCityOut,
    TripDayOut,
    TripItemOut,
    TripOut,
)
from app.modules.trips.totals import recalculate_total

DEFAULT_VISIT_MIN = 90
GAP_MIN = 30


# ---------- access checks (404 for other people's trips, so ids can't be probed) ----------


def get_own_trip(db: Session, user: User, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    return trip


def get_own_day(db: Session, trip: Trip, day_id: int) -> TripDay:
    day = db.get(TripDay, day_id)
    if day is None or day.trip_id != trip.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Day not found in this trip")
    return day


def get_own_item(db: Session, user: User, item_id: int) -> tuple[TripItem, TripDay, Trip]:
    row = db.execute(
        select(TripItem, TripDay, Trip)
        .join(TripDay, TripDay.id == TripItem.trip_day_id)
        .join(Trip, Trip.id == TripDay.trip_id)
        .where(TripItem.id == item_id, Trip.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return row[0], row[1], row[2]


def touch(trip: Trip) -> None:
    """Bumps updated_at even when only child rows (days, items) changed."""
    trip.updated_at = datetime.now().astimezone()


# ---------- generate ----------


def rank_cities_by_interests(db: Session, interest_ids: list[int]) -> list[tuple[City, int]]:
    """Every city with how many of its places match the interests, best first. Shared with GET /cities/suggest."""
    matching = select(Place.city_id, func.count(func.distinct(Place.id)).label("n"))
    if interest_ids:
        matching = matching.join(PlaceInterest, PlaceInterest.place_id == Place.id).where(
            PlaceInterest.interest_id.in_(interest_ids)
        )
    matching = matching.group_by(Place.city_id).subquery()
    rows = db.execute(
        select(City, func.coalesce(matching.c.n, 0))
        .outerjoin(matching, matching.c.city_id == City.id)
        .order_by(func.coalesce(matching.c.n, 0).desc(), City.id)
    ).all()
    return [(city, n) for city, n in rows]


def resolve_cities(db: Session, body: GenerateTripIn) -> list[int]:
    if body.city_ids:
        city_ids = list(dict.fromkeys(body.city_ids))  # drop repeats, keep order
        found = set(db.scalars(select(City.id).where(City.id.in_(city_ids))))
        missing = [c for c in city_ids if c not in found]
        if missing:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown city ids: {missing}")
        if len(city_ids) > body.days:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"{len(city_ids)} cities don't fit in {body.days} day(s); pick at most {body.days}",
            )
        return city_ids
    ranked = [city.id for city, n in rank_cities_by_interests(db, body.interest_ids) if n > 0]
    if not ranked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No city has places for these interests yet")
    return ranked[: recommended_city_count(body.days)]


def candidate_places(db: Session, city_ids: list[int]) -> list[CandidatePlace]:
    places = list(db.scalars(select(Place).where(Place.city_id.in_(city_ids)).order_by(Place.id)))
    interests: dict[int, list[int]] = {}
    for place_id, interest_id in db.execute(
        select(PlaceInterest.place_id, PlaceInterest.interest_id).where(
            PlaceInterest.place_id.in_([p.id for p in places])
        )
    ):
        interests.setdefault(place_id, []).append(interest_id)
    return [
        CandidatePlace(
            place_id=p.id,
            city_id=p.city_id,
            name=p.name,
            visit_minutes=p.visit_minutes,
            ticket_price=p.ticket_price,
            interest_ids=interests.get(p.id, []),
        )
        for p in places
    ]


def build_plan(
    db: Session,
    *,
    days: int,
    budget_level: str,
    budget_total: int | None,
    interest_ids: list[int],
    city_ids: list[int],
    variant: int = 0,
) -> PlanOut:
    places = candidate_places(db, city_ids)
    offers = [CandidateOffer(**o) for o in best_offers_for_cities(db, city_ids, budget_level)]
    return plan_trip(
        PlanIn(
            days=days,
            budget_level=budget_level,
            budget_total=budget_total,
            interest_ids=interest_ids,
            city_ids=city_ids,
            places=places,
            offers=offers,
            variant=variant,
        )
    )


def parse_hhmm(value: str | None) -> time | None:
    return time.fromisoformat(value) if value else None


def save_plan(db: Session, trip: Trip, plan: PlanOut, city_ids: list[int]) -> None:
    """Writes the planner's days and items. Ignores anything the planner made up (unknown places or offers)."""
    names = dict(db.execute(select(City.id, City.name).where(City.id.in_(city_ids))).all())
    allowed_places = set(db.scalars(select(Place.id).where(Place.city_id.in_(city_ids))))
    allowed_offers = {o["offer_id"] for o in best_offers_for_cities(db, city_ids, trip.budget_level, per_city=50)}
    used_places: set[int] = set()
    for planned in plan.days:
        if planned.city_id not in names:
            continue
        day = TripDay(
            trip_id=trip.id,
            day_number=planned.day_number,
            city_id=planned.city_id,
            title=planned.title or f"{names[planned.city_id]} · Day {planned.day_number}",
            offer_id=planned.offer_id if planned.offer_id in allowed_offers else None,
        )
        db.add(day)
        db.flush()
        position = 0
        for item in planned.items:
            if item.place_id is not None and (item.place_id not in allowed_places or item.place_id in used_places):
                continue
            if item.place_id is not None:
                used_places.add(item.place_id)
            db.add(
                TripItem(
                    trip_day_id=day.id,
                    place_id=item.place_id,
                    type=item.type,
                    start_time=parse_hhmm(item.start_time),
                    end_time=parse_hhmm(item.end_time),
                    note=item.note,
                    cost=item.cost,
                    position=position,
                )
            )
            position += 1
    db.flush()


def default_title(db: Session, days: int, city_ids: list[int]) -> str:
    names = dict(db.execute(select(City.id, City.name).where(City.id.in_(city_ids))).all())
    return f"{days} day{'s' if days > 1 else ''} in {' & '.join(names[c] for c in city_ids)}"


def generate_trip(db: Session, user: User, body: GenerateTripIn) -> Trip:
    ensure_interests_exist(db, body.interest_ids)
    interest_ids = list(dict.fromkeys(body.interest_ids))
    city_ids = resolve_cities(db, body)
    plan = build_plan(
        db,
        days=body.days,
        budget_level=body.budget_level,
        budget_total=body.budget_total,
        interest_ids=interest_ids,
        city_ids=city_ids,
    )
    trip = Trip(
        user_id=user.id,
        title=default_title(db, body.days, city_ids),
        start_date=body.start_date,
        days=body.days,
        budget_level=body.budget_level,
        budget_total=body.budget_total,
        suggest_destinations=not body.city_ids,
    )
    db.add(trip)
    db.flush()
    db.add_all(TripInterest(trip_id=trip.id, interest_id=i) for i in interest_ids)
    db.add_all(TripCity(trip_id=trip.id, city_id=c, position=n) for n, c in enumerate(city_ids))
    save_plan(db, trip, plan, city_ids)
    recalculate_total(db, trip.id)
    return trip


def trip_city_ids(db: Session, trip_id: int) -> list[int]:
    return list(db.scalars(select(TripCity.city_id).where(TripCity.trip_id == trip_id).order_by(TripCity.position)))


def trip_interest_ids(db: Session, trip_id: int) -> list[int]:
    return list(
        db.scalars(
            select(TripInterest.interest_id).where(TripInterest.trip_id == trip_id).order_by(TripInterest.interest_id)
        )
    )


def regenerate_trip(db: Session, trip: Trip, variant: int) -> Trip:
    """Same preferences, new plan. The old days and items are replaced; title and dates stay."""
    city_ids = trip_city_ids(db, trip.id)
    plan = build_plan(
        db,
        days=trip.days,
        budget_level=trip.budget_level,
        budget_total=trip.budget_total,
        interest_ids=trip_interest_ids(db, trip.id),
        city_ids=city_ids,
        variant=variant,
    )
    db.execute(delete(TripDay).where(TripDay.trip_id == trip.id))
    db.flush()
    save_plan(db, trip, plan, city_ids)
    recalculate_total(db, trip.id)
    touch(trip)
    return trip


def change_days(db: Session, trip: Trip, new_days: int) -> None:
    """Fewer days: the last days are removed. More days: empty days are added in the last day's city."""
    days = list(db.scalars(select(TripDay).where(TripDay.trip_id == trip.id).order_by(TripDay.day_number)))
    if new_days < len(days):
        for day in days[new_days:]:
            db.delete(day)
    elif days:
        last = days[-1]
        city_name = db.scalar(select(City.name).where(City.id == last.city_id))
        for n in range(len(days) + 1, new_days + 1):
            db.add(
                TripDay(
                    trip_id=trip.id,
                    day_number=n,
                    city_id=last.city_id,
                    offer_id=last.offer_id,
                    title=f"{city_name} · Day {n}",
                )
            )
    trip.days = new_days
    db.flush()


# ---------- items ----------


def to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def from_minutes(m: int) -> time:
    m = max(0, min(m, 23 * 60 + 59))
    return time(m // 60, m % 60)


def next_free_time(db: Session, day: TripDay) -> time:
    """Right after the day's last item, or 09:00 for an empty day."""
    last_end = db.scalar(
        select(func.max(func.coalesce(TripItem.end_time, TripItem.start_time))).where(TripItem.trip_day_id == day.id)
    )
    return from_minutes(to_minutes(last_end) + GAP_MIN) if last_end else time(9, 0)


def reflow_times(items: list[TripItem]) -> None:
    """After a reorder: keep each item's length, start from the day's earliest time, 30 minutes between items."""
    timed = [i for i in items if i.start_time]
    if not timed:
        return
    clock = min(to_minutes(i.start_time) for i in timed)
    for item in items:
        if not item.start_time:
            continue
        length = to_minutes(item.end_time) - to_minutes(item.start_time) if item.end_time else None
        item.start_time = from_minutes(clock)
        if length is not None:
            item.end_time = from_minutes(clock + length)
        clock += (length or 0) + GAP_MIN


def renumber(db: Session, day_id: int) -> None:
    items = db.scalars(select(TripItem).where(TripItem.trip_day_id == day_id).order_by(TripItem.position, TripItem.id))
    for n, item in enumerate(items):
        item.position = n


# ---------- choosing a hotel offer for a night ----------


def check_offer_for_day(db: Session, trip: Trip, day: TripDay, offer_id: int) -> Offer:
    row = db.execute(
        select(Offer, Company, Hotel)
        .join(Company, Company.id == Offer.company_id)
        .join(Hotel, Hotel.id == Offer.hotel_id)
        .where(Offer.id == offer_id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Offer not found")
    offer, company, hotel = row
    expired = offer.valid_to is not None and offer.valid_to < date.today()
    if offer.status != "active" or company.status != "approved" or expired:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This offer is not available any more")
    if hotel.city_id != day.city_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This hotel is not in the day's city")
    night = day_date(trip, day) or date.today()
    if (offer.valid_from and night < offer.valid_from) or (offer.valid_to and night > offer.valid_to):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"This offer is not valid on {night.isoformat()}")
    return offer


# ---------- reading a trip for the screens ----------


def day_date(trip: Trip, day: TripDay) -> date | None:
    return trip.start_date + timedelta(days=day.day_number - 1) if trip.start_date else None


def to_trip_out(db: Session, trip: Trip) -> TripOut:
    city_ids = trip_city_ids(db, trip.id)
    days = list(db.scalars(select(TripDay).where(TripDay.trip_id == trip.id).order_by(TripDay.day_number)))
    all_city_ids = set(city_ids) | {d.city_id for d in days}
    names = dict(db.execute(select(City.id, City.name).where(City.id.in_(all_city_ids))).all())

    items_by_day: dict[int, list[TripItemOut]] = {d.id: [] for d in days}
    rows = db.execute(
        select(TripItem, Place.name, Place.image_url)
        .outerjoin(Place, Place.id == TripItem.place_id)
        .where(TripItem.trip_day_id.in_(items_by_day))
        .order_by(TripItem.position, TripItem.id)
    ).all()
    for item, place_name, image_url in rows:
        items_by_day[item.trip_day_id].append(
            TripItemOut(
                id=item.id,
                place_id=item.place_id,
                place_name=place_name,
                place_image_url=image_url,
                type=item.type,
                start_time=item.start_time,
                end_time=item.end_time,
                note=item.note,
                cost=item.cost,
                position=item.position,
            )
        )

    offer_ids = {d.offer_id for d in days if d.offer_id}
    hotels: dict[int, DayHotelOut] = {}
    for offer, hotel, company in db.execute(
        select(Offer, Hotel, Company)
        .join(Hotel, Hotel.id == Offer.hotel_id)
        .join(Company, Company.id == Offer.company_id)
        .where(Offer.id.in_(offer_ids))
    ).all():
        hotels[offer.id] = DayHotelOut(
            offer_id=offer.id,
            hotel_id=hotel.id,
            hotel_name=hotel.name,
            stars=hotel.stars,
            company_id=company.id,
            company_name=company.name,
            room_type=offer.room_type,
            price_per_night=offer.price_per_night,
            free_cancellation=offer.free_cancellation,
            breakfast_included=offer.breakfast_included,
        )

    itinerary = []
    for d in days:
        hotel = hotels.get(d.offer_id) if d.offer_id else None
        items = items_by_day[d.id]
        itinerary.append(
            TripDayOut(
                id=d.id,
                day_number=d.day_number,
                date=day_date(trip, d),
                city_id=d.city_id,
                city_name=names.get(d.city_id, ""),
                title=d.title,
                hotel=hotel,
                items=items,
                day_cost=sum(i.cost for i in items) + (hotel.price_per_night if hotel else 0),
            )
        )

    return TripOut(
        id=trip.id,
        title=trip.title,
        status=trip.status,
        start_date=trip.start_date,
        end_date=trip.start_date + timedelta(days=trip.days - 1) if trip.start_date else None,
        days=trip.days,
        budget_level=trip.budget_level,
        budget_total=trip.budget_total,
        total_cost=trip.total_cost,
        over_budget=trip.budget_total is not None and trip.total_cost > trip.budget_total,
        interest_ids=trip_interest_ids(db, trip.id),
        cities=[TripCityOut(id=c, name=names[c]) for c in city_ids],
        itinerary=itinerary,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


def to_card(db: Session, trip: Trip) -> TripCardOut:
    cities = list(
        db.scalars(
            select(City.name)
            .join(TripCity, TripCity.city_id == City.id)
            .where(TripCity.trip_id == trip.id)
            .order_by(TripCity.position)
        )
    )
    return TripCardOut(
        id=trip.id,
        title=trip.title,
        status=trip.status,
        start_date=trip.start_date,
        days=trip.days,
        cities=cities,
        total_cost=trip.total_cost,
        budget_total=trip.budget_total,
        created_at=trip.created_at,
    )
