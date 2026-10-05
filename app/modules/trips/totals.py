"""Shared trip total calculation. Owner: Person 2.

Everyone who changes a trip calls recalculate_total(db, trip_id) after the change:
adding/removing items (Person 2), chat Keep/Undo (Person 3), choosing a hotel offer (Person 6).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.offers.models import Offer
from app.modules.trips.models import Trip, TripDay, TripItem


def recalculate_total(db: Session, trip_id: int) -> int:
    items_cost = db.scalar(
        select(func.coalesce(func.sum(TripItem.cost), 0))
        .join(TripDay, TripItem.trip_day_id == TripDay.id)
        .where(TripDay.trip_id == trip_id)
    )
    hotels_cost = db.scalar(
        select(func.coalesce(func.sum(Offer.price_per_night), 0))
        .join(TripDay, TripDay.offer_id == Offer.id)
        .where(TripDay.trip_id == trip_id)
    )
    total = int(items_cost or 0) + int(hotels_cost or 0)
    trip = db.get(Trip, trip_id)
    if trip is not None:
        trip.total_cost = total
        db.add(trip)
    return total
