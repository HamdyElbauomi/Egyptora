"""Feature A3 (offers part) · Admin offers and price flags."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate
from app.modules.accounts.models import User
from app.modules.companies.models import Company
from app.modules.hotels.models import Hotel
from app.modules.offers.models import OFFER_STATUSES, Offer, PriceAlert
from app.modules.offers.schemas import AdminOfferOut, FlagIn, OfferOut
from app.modules.offers.service import get_offer_or_404, market_median

router = APIRouter(prefix="/admin/offers", tags=["A3 · Admin offers"])
admin = require_role("admin")
LOW_PRICE_RATIO = 0.5


def to_admin_out(db: Session, offer: Offer) -> AdminOfferOut:
    med = market_median(db, offer)
    check = "low" if med and offer.price_per_night < LOW_PRICE_RATIO * med else None
    return AdminOfferOut(
        **OfferOut.model_validate(offer).model_dump(),
        hotel_name=db.scalar(select(Hotel.name).where(Hotel.id == offer.hotel_id)),
        company_name=db.scalar(select(Company.name).where(Company.id == offer.company_id)),
        market_median=med,
        price_check=check,
    )


@router.get("", response_model=Page[AdminOfferOut])
def list_offers(
    status_filter: str | None = Query(None, alias="status", pattern=f"^({'|'.join(OFFER_STATUSES)})$"),
    hotel_id: int | None = None,
    company_id: int | None = None,
    params: PageParams = Depends(),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> Page[AdminOfferOut]:
    """Why: the admin watches all offers for fake or mistyped prices.
    Each offer shows the median price of its competitors and price_check="low" when it's under half of it.
    Then: flag suspicious ones with POST /admin/offers/{id}/flag."""
    stmt = select(Offer).order_by(Offer.hotel_id, Offer.room_type, Offer.price_per_night)
    if status_filter:
        stmt = stmt.where(Offer.status == status_filter)
    if hotel_id is not None:
        stmt = stmt.where(Offer.hotel_id == hotel_id)
    if company_id is not None:
        stmt = stmt.where(Offer.company_id == company_id)
    offers, total = paginate(db, stmt, params)
    return Page(data=[to_admin_out(db, o) for o in offers], page=params.page, limit=params.limit, total=total)


@router.post("/{offer_id}/flag", response_model=AdminOfferOut)
def flag_offer(
    offer_id: int, body: FlagIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> AdminOfferOut:
    """Why: a price far below the market is a mistake or a scam.
    Effect: the offer is hidden from travelers, and the company gets a price_anomaly alert with the reason.
    The company can't resume it until the admin unflags it."""
    offer = get_offer_or_404(db, offer_id)
    if offer.status == "flagged":
        raise HTTPException(status.HTTP_409_CONFLICT, "Offer is already flagged")
    offer.status = "flagged"
    offer.flag_reason = body.reason
    db.add(
        PriceAlert(
            company_id=offer.company_id,
            offer_id=offer.id,
            type="price_anomaly",
            message=f'Your "{offer.room_type}" offer was hidden by Egyptora for review: {body.reason}',
        )
    )
    db.commit()
    db.refresh(offer)
    return to_admin_out(db, offer)


@router.post("/{offer_id}/unflag", response_model=AdminOfferOut)
def unflag_offer(offer_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> AdminOfferOut:
    """Why: the admin checked and the price is real.
    Effect: the offer goes back to active, or to paused when its company is not approved right now."""
    offer = get_offer_or_404(db, offer_id)
    if offer.status != "flagged":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Offer is {offer.status}, not flagged")
    company_status = db.scalar(select(Company.status).where(Company.id == offer.company_id))
    offer.status = "active" if company_status == "approved" else "paused"
    offer.flag_reason = None
    db.commit()
    db.refresh(offer)
    return to_admin_out(db, offer)
