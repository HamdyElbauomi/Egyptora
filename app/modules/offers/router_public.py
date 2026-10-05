"""Feature T8 · Compare offers and choose one (traveler side). Owner: Person 6."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.offers.schemas import ChooseOfferIn

router = APIRouter(tags=["T8 · Compare offers"])
OWNER = "Person 6"


@router.get("/hotels/{hotel_id}/offers")
def hotel_offers(
    hotel_id: int, sort: str = Query("best_value", pattern="^(lowest|best_value)$"), db: Session = Depends(get_db)
):
    """Why: the traveler compares every company's offer for the same hotel, with Lowest and Best value badges
    (ranking.py). Then: chooses one with PUT /trips/{id}/days/{dayId}/offer."""
    raise not_implemented(OWNER)


@router.put("/trips/{trip_id}/days/{day_id}/offer")
def choose_offer(
    trip_id: int,
    day_id: int,
    body: ChooseOfferIn,
    user: User = Depends(require_role("traveler")),
    db: Session = Depends(get_db),
):
    """Why: the traveler picks which company they book that night with.
    Then: sets trip_days.offer_id, calls trips/totals.recalculate_total(),
    and counts as "chosen" in the company dashboard."""
    raise not_implemented(OWNER)
