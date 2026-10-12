"""Features T3, T4 · Build the trip, view and edit it. Owner: Person 2.

Every endpoint here only touches the logged-in traveler's own trips: someone else's trip id gives 404.
Every change returns the whole updated trip (same shape as GET /trips/{id}), so the screen can redraw
the timeline and the total in one go.
"""

import random

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.accounts.models import User
from app.modules.places.models import Place
from app.modules.trips.models import Trip, TripDay, TripItem
from app.modules.trips.schemas import (
    AddItemIn,
    ChooseOfferIn,
    GenerateTripIn,
    ReorderIn,
    TripCardOut,
    TripOut,
    UpdateItemIn,
    UpdateTripIn,
)
from app.modules.trips.service import (
    DEFAULT_VISIT_MIN,
    change_days,
    check_offer_for_day,
    from_minutes,
    generate_trip,
    get_own_day,
    get_own_item,
    get_own_trip,
    next_free_time,
    reflow_times,
    regenerate_trip,
    renumber,
    to_card,
    to_minutes,
    to_trip_out,
    touch,
)
from app.modules.trips.totals import recalculate_total

router = APIRouter(tags=["T3-T4 · Trips"])
traveler = require_role("traveler")


def saved(db: Session, trip: Trip) -> TripOut:
    """Recalculates the total, commits and returns the full trip."""
    recalculate_total(db, trip.id)
    touch(trip)
    db.commit()
    db.refresh(trip)
    return to_trip_out(db, trip)


# ---------- T3 · build ----------


@router.post("/trips/generate", status_code=201, response_model=TripOut)
def generate(body: GenerateTripIn, user: User = Depends(traveler), db: Session = Depends(get_db)) -> TripOut:
    """AI. Why: the main promise of Egyptora: preferences in, complete trip out.
    How: picks the cities (yours, or the best match for your interests when suggest=true),
    collects their places and the best hotel offer per city for your budget level,
    then the planner (app/ai/planner.py) fills each day from 09:00 to 18:00 without repeating a place.
    With budget_total, the hotel is the best one that still fits the money left per night.
    Then: the Home screen shows the result. Change it with the endpoints below or with the chat."""
    trip = generate_trip(db, user, body)
    db.commit()
    db.refresh(trip)
    return to_trip_out(db, trip)


@router.post("/trips/{trip_id}/regenerate", response_model=TripOut)
def regenerate(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> TripOut:
    """AI. Why: the traveler doesn't like the plan and wants another version.
    How: same preferences (interests, cities, days, budget), a different plan. Hand edits are replaced.
    Title, start date and the trip id stay the same."""
    trip = get_own_trip(db, user, trip_id)
    regenerate_trip(db, trip, variant=random.randint(1, 1000))
    db.commit()
    db.refresh(trip)
    return to_trip_out(db, trip)


# ---------- T4 · view and edit ----------


@router.get("/trips", response_model=list[TripCardOut])
def my_trips(user: User = Depends(traveler), db: Session = Depends(get_db)) -> list[TripCardOut]:
    """Why: the traveler returns and needs their trips (newest first), drafts and saved ones.
    Then: opens one trip with GET /trips/{id}."""
    trips = db.scalars(select(Trip).where(Trip.user_id == user.id).order_by(Trip.created_at.desc(), Trip.id.desc()))
    return [to_card(db, t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> TripOut:
    """Why: Home shows day tabs, each day's timeline, tonight's hotel, the day cost and the trip total.
    over_budget is true when the total is above budget_total.
    Then: chat and summary (Person 3) read the same trip."""
    return to_trip_out(db, get_own_trip(db, user, trip_id))


@router.patch("/trips/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: int, body: UpdateTripIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> TripOut:
    """Why: the traveler changes the title, start date, budget or number of days.
    Fewer days removes the last days. More days adds empty days in the last city (same hotel);
    fill them by hand or with regenerate."""
    trip = get_own_trip(db, user, trip_id)
    changes = body.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise HTTPException(422, "title can't be empty")
    new_days = changes.pop("days", None)
    if new_days is not None and new_days != trip.days:
        change_days(db, trip, new_days)
    for field, value in changes.items():
        setattr(trip, field, value)
    return saved(db, trip)


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> Response:
    """Why: remove a trip the traveler no longer wants. Its days, items and chat go with it."""
    trip = get_own_trip(db, user, trip_id)
    db.delete(trip)
    db.commit()
    return Response(status_code=204)


@router.post("/trips/{trip_id}/days/{day_id}/items", status_code=201, response_model=TripOut)
def add_item(
    trip_id: int, day_id: int, body: AddItemIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> TripOut:
    """Why: add a place by hand, or add a scanned monument from the camera (Person 4).
    Rules: the place must be in the day's city and not already in the trip.
    Empty start_time = right after the day's last item; empty end_time = start + the place's visit length;
    empty cost = the place's ticket price. It goes at the end of the day."""
    trip = get_own_trip(db, user, trip_id)
    day = get_own_day(db, trip, day_id)
    place = None
    if body.place_id is not None:
        place = db.get(Place, body.place_id)
        if place is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Place not found")
        if place.city_id != day.city_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{place.name} is not in this day's city")
        already = db.scalar(
            select(TripDay.day_number)
            .join(TripItem, TripItem.trip_day_id == TripDay.id)
            .where(TripDay.trip_id == trip.id, TripItem.place_id == place.id)
        )
        if already:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{place.name} is already on day {already}")

    start = body.start_time or next_free_time(db, day)
    end = body.end_time
    if end is None and place is not None:
        end = from_minutes(to_minutes(start) + (place.visit_minutes or DEFAULT_VISIT_MIN))
    cost = body.cost if body.cost is not None else ((place.ticket_price or 0) if place else 0)
    last = db.scalar(select(func.max(TripItem.position)).where(TripItem.trip_day_id == day.id))
    db.add(
        TripItem(
            trip_day_id=day.id,
            place_id=body.place_id,
            type=body.type,
            start_time=start,
            end_time=end,
            note=body.note,
            cost=cost,
            position=(last + 1) if last is not None else 0,
        )
    )
    db.flush()
    return saved(db, trip)


@router.patch("/trip-items/{item_id}", response_model=TripOut)
def update_item(
    item_id: int, body: UpdateItemIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> TripOut:
    """Why: change an item's time, note or cost. Send only the fields that change."""
    item, _, trip = get_own_item(db, user, item_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("cost", 0) is None:
        raise HTTPException(422, "cost can't be empty; send 0")
    for field, value in changes.items():
        setattr(item, field, value)
    if item.start_time and item.end_time and item.end_time < item.start_time:
        raise HTTPException(422, "end_time must be after start_time")
    return saved(db, trip)


@router.delete("/trip-items/{item_id}", status_code=204)
def delete_item(item_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> Response:
    """Why: remove something from a day. The total is recalculated."""
    item, day, trip = get_own_item(db, user, item_id)
    db.delete(item)
    db.flush()
    renumber(db, day.id)
    saved(db, trip)
    return Response(status_code=204)


@router.put("/trips/{trip_id}/days/{day_id}/order", response_model=TripOut)
def reorder_items(
    trip_id: int, day_id: int, body: ReorderIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> TripOut:
    """Why: drag to reorder the day's timeline.
    Send every item id of the day in the new order. Times move with the order: each item keeps its length,
    the day starts at its earliest time, with 30 minutes between items."""
    trip = get_own_trip(db, user, trip_id)
    day = get_own_day(db, trip, day_id)
    items = {i.id: i for i in db.scalars(select(TripItem).where(TripItem.trip_day_id == day.id))}
    if sorted(body.item_ids) != sorted(items):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"item_ids must be exactly this day's items: {sorted(items)}")
    ordered = [items[i] for i in body.item_ids]
    for n, item in enumerate(ordered):
        item.position = n
    reflow_times(ordered)
    return saved(db, trip)


@router.put("/trips/{trip_id}/days/{day_id}/offer", response_model=TripOut)
def choose_offer(
    trip_id: int,
    day_id: int,
    body: ChooseOfferIn,
    user: User = Depends(traveler),
    db: Session = Depends(get_db),
) -> TripOut:
    """Why: the traveler picks which company they book that night with (from GET /hotels/{id}/offers).
    Rules: the offer must be live, in the day's city, and valid on that night's date. offer_id=null removes it.
    The total is recalculated; the company's dashboard counts it in times_chosen."""
    trip = get_own_trip(db, user, trip_id)
    day = get_own_day(db, trip, day_id)
    day.offer_id = check_offer_for_day(db, trip, day, body.offer_id).id if body.offer_id is not None else None
    return saved(db, trip)
