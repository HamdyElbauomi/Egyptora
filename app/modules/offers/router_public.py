"""Feature T8 · Compare offers for a hotel (traveler side).

Choosing an offer for a night (PUT /trips/{id}/days/{dayId}/offer) lives with the trips feature,
because it changes a trip.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.companies.models import Company
from app.modules.companies.service import to_public_out
from app.modules.hotels.service import get_hotel_or_404
from app.modules.offers.models import Offer
from app.modules.offers.ranking import OfferForRanking, rank
from app.modules.offers.schemas import HotelOffersOut, PublicOfferOut
from app.modules.offers.service import live_conditions

router = APIRouter(tags=["T8 · Compare offers"])


@router.get("/hotels/{hotel_id}/offers", response_model=HotelOffersOut)
def hotel_offers(
    hotel_id: int,
    sort: str = Query("best_value", pattern="^(lowest|best_value)$"),
    room_type: str | None = Query(None, description="Only this room type, e.g. Double"),
    db: Session = Depends(get_db),
) -> HotelOffersOut:
    """Why: the traveler compares every company's offer for the same hotel. Public, no login.
    Only live offers show: active, from an approved company, not past valid_to.
    Badges: is_lowest = cheapest; is_best_value = best mix of price (50%), company trust (35%)
    and free cancellation (15%), see offers/ranking.py.
    Then: the traveler picks one for a night with PUT /trips/{id}/days/{dayId}/offer."""
    hotel = get_hotel_or_404(db, hotel_id)
    stmt = (
        select(Offer, Company)
        .join(Company, Company.id == Offer.company_id)
        .where(Offer.hotel_id == hotel_id, live_conditions())
    )
    if room_type:
        stmt = stmt.where(Offer.room_type.ilike(room_type))
    rows = db.execute(stmt).all()

    ranking = rank(
        [
            OfferForRanking(
                o.id, o.price_per_night, float(c.trust_score) if c.trust_score else None, o.free_cancellation
            )
            for o, c in rows
        ]
    )
    by_id = {o.id: (o, c) for o, c in rows}
    order = ranking["order"] if sort == "best_value" else sorted(by_id, key=lambda i: (by_id[i][0].price_per_night, i))
    offers = [
        PublicOfferOut(
            offer_id=o.id,
            room_type=o.room_type,
            price_per_night=o.price_per_night,
            breakfast_included=o.breakfast_included,
            free_cancellation=o.free_cancellation,
            cancellation_days=o.cancellation_days,
            valid_to=o.valid_to,
            company=to_public_out(c),
            is_lowest=o.price_per_night == by_id[ranking["lowest"]][0].price_per_night,
            is_best_value=o.id == ranking["best_value"],
        )
        for o, c in (by_id[i] for i in order)
    ]
    return HotelOffersOut(hotel_id=hotel.id, hotel_name=hotel.name, offers=offers)
