"""Features C3, C4 · Company offers, dashboard and competition. Owner: Person 6.

Every route here needs role=company AND the company's status = approved (Person 1's companies table).
"""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.offers.schemas import OfferIn, OfferUpdateIn

router = APIRouter(prefix="/company", tags=["C3-C4 · Company offers"])
OWNER = "Person 6"
company = require_role("company")


@router.get("/hotels")
def hotels_to_sell(
    search: str | None = None, city_id: int | None = None, user: User = Depends(company), db: Session = Depends(get_db)
):
    """Why: a company needs to find the hotel it wants to sell.
    Then: picks one in POST /company/offers."""
    raise not_implemented(OWNER)


@router.get("/offers")
def my_offers(status: str | None = None, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the company manages all its offers in one list, each with its market position.
    Then: edit, pause or delete from here."""
    raise not_implemented(OWNER)


@router.post("/offers", status_code=201)
def create_offer(body: OfferIn, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the company sets its own price, room type and cancellation terms for a hotel.
    Then: the offer competes with other companies' offers for the same hotel."""
    raise not_implemented(OWNER)


@router.patch("/offers/{offer_id}")
def update_offer(offer_id: int, body: OfferUpdateIn, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: prices change with the season and the competition.
    Then: may trigger undercut alerts for other companies (service.create_undercut_alerts)."""
    raise not_implemented(OWNER)


@router.post("/offers/{offer_id}/pause")
def pause_offer(offer_id: int, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: hotel is full or the deal ended, but the company wants to keep the offer.
    Then: hidden from travelers and from search."""
    raise not_implemented(OWNER)


@router.post("/offers/{offer_id}/resume")
def resume_offer(offer_id: int, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the room is available again. Then: visible again."""
    raise not_implemented(OWNER)


@router.delete("/offers/{offer_id}", status_code=204)
def delete_offer(offer_id: int, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: remove an offer for good."""
    raise not_implemented(OWNER)


@router.post("/offers/import", status_code=201)
async def import_offers(file: UploadFile, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: companies with many hotels upload a CSV instead of typing each offer."""
    raise not_implemented(OWNER)


@router.get("/dashboard")
def dashboard(user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the company's first screen: active offers, how often travelers chose them, trust score, open alerts."""
    raise not_implemented(OWNER)


@router.get("/offers/{offer_id}/market")
def offer_market(offer_id: int, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the company wants to know "am I the cheapest?": position (#3 of 4), lowest price, gap, Best value rank.
    Then: pushes companies to lower prices or improve terms, which is the competition."""
    raise not_implemented(OWNER)


@router.get("/alerts")
def alerts(user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: the company should know right away when a competitor goes lower or the admin flags its price."""
    raise not_implemented(OWNER)


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, user: User = Depends(company), db: Session = Depends(get_db)):
    """Why: clear alerts already seen."""
    raise not_implemented(OWNER)
