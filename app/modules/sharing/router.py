"""Feature T10 · Summary, save and share. Owner: Person 3."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User

router = APIRouter(tags=["T10 · Summary and share"])
OWNER = "Person 3"
traveler = require_role("traveler")


@router.get("/trips/{trip_id}/summary")
def trip_summary(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: before saving, the traveler wants the total split into hotels, tickets and other costs.
    Then: Summary screen."""
    raise not_implemented(OWNER)


@router.post("/trips/{trip_id}/save")
def save_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: marks the trip as final instead of a draft.
    Then: the trip shows as saved in GET /trips."""
    raise not_implemented(OWNER)


@router.post("/trips/{trip_id}/share")
def share_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: travelers plan with family and friends.
    Then: creates share_token (use secrets.token_urlsafe), used by GET /shared/{token}."""
    raise not_implemented(OWNER)


@router.delete("/trips/{trip_id}/share", status_code=204)
def unshare_trip(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: stop a link that was shared by mistake.
    Then: GET /shared/{token} stops working for that token."""
    raise not_implemented(OWNER)


@router.get("/shared/{token}")
def shared_trip(token: str, db: Session = Depends(get_db)):
    """Why: people without an account open the shared link.
    Then: read-only trip view, no login."""
    raise not_implemented(OWNER)
