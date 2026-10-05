"""Features T3, T4 · Build the trip, view and edit it. Owner: Person 2."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.trips.schemas import AddItemIn, GenerateTripIn, ReorderIn, UpdateItemIn, UpdateTripIn

router = APIRouter(tags=["T3-T4 · Trips"])
OWNER = "Person 2"
traveler = require_role("traveler")


@router.post("/trips/generate", status_code=201)
def generate(body: GenerateTripIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """AI. Why: the main promise of Egyptora: preferences in, complete trip out.
    Then: collects places (Person 4) and best offers per city (Person 6), calls app/ai/planner.py,
    saves days and items (service.py). The Home screen shows the result."""
    raise not_implemented(OWNER)


@router.post("/trips/{trip_id}/regenerate")
def regenerate(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """AI. Why: the traveler doesn't like the plan and wants another version.
    Then: same as generate, with the same preferences."""
    raise not_implemented(OWNER)


@router.get("/trips")
def my_trips(user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: the traveler returns and needs their saved trips.
    Then: opens one trip in GET /trips/{id}."""
    raise not_implemented(OWNER)


@router.get("/trips/{trip_id}")
def get_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: Home shows day tabs, timeline, tonight's hotel and the total.
    Then: chat and summary (Person 3) read the same trip."""
    raise not_implemented(OWNER)


@router.patch("/trips/{trip_id}")
def update_trip(trip_id: int, body: UpdateTripIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: the traveler changes the title, start date or number of days.
    Then: if days change, the plan may need regenerate."""
    raise not_implemented(OWNER)


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: remove a trip the traveler no longer wants."""
    raise not_implemented(OWNER)


@router.post("/trips/{trip_id}/days/{day_id}/items", status_code=201)
def add_item(trip_id: int, day_id: int, body: AddItemIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: add a place by hand, or add a scanned monument from the camera (Person 4).
    Then: call totals.recalculate_total()."""
    raise not_implemented(OWNER)


@router.patch("/trip-items/{item_id}")
def update_item(item_id: int, body: UpdateItemIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: change an item's time, note or cost.
    Then: call totals.recalculate_total()."""
    raise not_implemented(OWNER)


@router.delete("/trip-items/{item_id}", status_code=204)
def delete_item(item_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: remove something from a day.
    Then: call totals.recalculate_total()."""
    raise not_implemented(OWNER)


@router.put("/trips/{trip_id}/days/{day_id}/order")
def reorder_items(
    trip_id: int, day_id: int, body: ReorderIn, user: User = Depends(traveler), db: Session = Depends(get_db)
):
    """Why: drag to reorder the day's timeline."""
    raise not_implemented(OWNER)
