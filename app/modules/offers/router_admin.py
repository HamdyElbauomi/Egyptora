"""Feature A3 (offers part) · Admin offers and price flags. Owner: Person 6."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.offers.schemas import FlagIn

router = APIRouter(prefix="/admin/offers", tags=["A3 · Admin offers"])
OWNER = "Person 6"
admin = require_role("admin")


@router.get("")
def list_offers(status: str | None = None, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin watches all offers for fake or mistyped prices."""
    raise not_implemented(OWNER)


@router.post("/{offer_id}/flag")
def flag_offer(offer_id: int, body: FlagIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: a price far below the market is a mistake or a scam.
    Then: offer hidden, the company gets a price_anomaly alert."""
    raise not_implemented(OWNER)


@router.post("/{offer_id}/unflag")
def unflag_offer(offer_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin checked and the price is real. Then: offer visible again."""
    raise not_implemented(OWNER)
