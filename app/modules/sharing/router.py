"""Feature T10 · Summary, save and share. Owner: Person 3."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.accounts.models import User
from app.modules.sharing.schemas import SharedTripOut, ShareOut, SummaryOut
from app.modules.sharing.service import build_summary
from app.modules.trips.models import Trip
from app.modules.trips.schemas import TripOut
from app.modules.trips.service import get_own_trip, to_trip_out, touch

router = APIRouter(tags=["T10 · Summary and share"])
traveler = require_role("traveler")


@router.get("/trips/{trip_id}/summary", response_model=SummaryOut)
def trip_summary(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> SummaryOut:
    """Why: before saving, the traveler wants to see where the money goes.
    Gives the total split into hotels, tickets and other costs, the same split per city and per day,
    the hotels to book (nights grouped per offer), and how much budget is left (negative = over budget).
    Then: Summary screen, with Save and Share buttons."""
    trip = get_own_trip(db, user, trip_id)
    return build_summary(trip, to_trip_out(db, trip))


@router.post("/trips/{trip_id}/save", response_model=TripOut)
def save_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> TripOut:
    """Why: marks the trip as final instead of a draft. Saving twice is fine.
    The trip can still be edited after saving.
    Then: the trip shows as saved in GET /trips."""
    trip = get_own_trip(db, user, trip_id)
    trip.status = "saved"
    touch(trip)
    db.commit()
    return to_trip_out(db, trip)


@router.post("/trips/{trip_id}/share", response_model=ShareOut)
def share_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> ShareOut:
    """Why: travelers plan with family and friends.
    Creates a secret link token, or returns the existing one (sharing twice gives the same link).
    Anyone with the link sees the trip read-only, with its latest changes.
    Then: the front end shows {its own address}{share_path}, which calls GET /shared/{token}."""
    trip = get_own_trip(db, user, trip_id)
    if trip.share_token is None:
        trip.share_token = secrets.token_urlsafe(16)
        db.commit()
    return ShareOut(share_token=trip.share_token, share_path=f"/shared/{trip.share_token}")


@router.delete("/trips/{trip_id}/share", status_code=204)
def unshare_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> Response:
    """Why: stop a link that was shared by mistake.
    The old link stops working at once. Sharing again later gives a new link."""
    trip = get_own_trip(db, user, trip_id)
    trip.share_token = None
    db.commit()
    return Response(status_code=204)


@router.get("/shared/{token}", response_model=SharedTripOut)
def shared_trip(token: str, db: Session = Depends(get_db)) -> SharedTripOut:
    """Why: people without an account open the shared link. No login.
    Read-only: the plan, hotels and total, without the owner's budget or account details.
    Then: they can sign up and build their own trip."""
    trip = db.scalar(select(Trip).where(Trip.share_token == token))
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is not valid or was turned off")
    full = to_trip_out(db, trip)
    return SharedTripOut(
        title=full.title,
        start_date=full.start_date,
        end_date=full.end_date,
        days=full.days,
        cities=full.cities,
        total_cost=full.total_cost,
        itinerary=full.itinerary,
        updated_at=full.updated_at,
    )
