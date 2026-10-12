"""Offer logic shared by the company portal, admin, traveler pages and the trip planner.

An offer is "live" (travelers can see and book it) when:
    offer.status == "active" AND its company is approved AND valid_to is empty or not in the past.
"""

from datetime import date
from statistics import median

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.modules.accounts.models import User
from app.modules.catalog.models import City
from app.modules.companies.models import Company
from app.modules.companies.service import company_of
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer, PriceAlert
from app.modules.offers.ranking import OfferForRanking, rank
from app.modules.offers.schemas import MyOfferOut, OfferOut

BUDGET_ORDER = ("low", "mid", "high")


def live_conditions():
    today = date.today()
    return and_(
        Offer.status == "active",
        Company.status == "approved",
        or_(Offer.valid_to.is_(None), Offer.valid_to >= today),
    )


def approved_company_of(db: Session, user: User) -> Company:
    """Only approved companies can sell. Pending, rejected or suspended companies get 403 with the reason."""
    company = company_of(db, user)
    if company.status != "approved":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f"Your company is {company.status}; only approved companies can manage offers"
        )
    return company


def get_own_offer(db: Session, company: Company, offer_id: int) -> Offer:
    """Another company's offer looks exactly like a missing one (404), so ids can't be probed."""
    offer = db.get(Offer, offer_id)
    if offer is None or offer.company_id != company.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Offer {offer_id} not found")
    return offer


def get_offer_or_404(db: Session, offer_id: int) -> Offer:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Offer {offer_id} not found")
    return offer


def ensure_hotel_exists(db: Session, hotel_id: int) -> Hotel:
    hotel = db.get(Hotel, hotel_id)
    if hotel is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown hotel_id: {hotel_id}")
    return hotel


def ensure_room_free(db: Session, company_id: int, hotel_id: int, room_type: str, exclude_id: int | None = None):
    """One offer per company, hotel and room type: change the price instead of adding a second offer."""
    stmt = select(Offer.id).where(
        Offer.company_id == company_id,
        Offer.hotel_id == hotel_id,
        func.lower(Offer.room_type) == room_type.strip().lower(),
    )
    if exclude_id is not None:
        stmt = stmt.where(Offer.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f'You already have a "{room_type}" offer for this hotel; edit it instead'
        )


def live_competition(db: Session, hotel_id: int, room_type: str) -> list[tuple[Offer, Company]]:
    """All live offers for the same hotel and room type, cheapest first."""
    rows = db.execute(
        select(Offer, Company)
        .join(Company, Company.id == Offer.company_id)
        .where(Offer.hotel_id == hotel_id, func.lower(Offer.room_type) == room_type.lower(), live_conditions())
        .order_by(Offer.price_per_night, Offer.id)
    ).all()
    return [(o, c) for o, c in rows]


def position_of(offer: Offer, competition: list[tuple[Offer, Company]]) -> tuple[int | None, int, int | None]:
    """(position, total, lowest price). Ties share the better position: two offers at 1200 are both #1."""
    prices = [o.price_per_night for o, _ in competition]
    lowest = prices[0] if prices else None
    if not any(o.id == offer.id for o, _ in competition):
        return None, len(prices), lowest
    position = 1 + sum(1 for p in prices if p < offer.price_per_night)
    return position, len(prices), lowest


def best_value_rank(offer: Offer, competition: list[tuple[Offer, Company]]) -> int | None:
    items = [
        OfferForRanking(o.id, o.price_per_night, float(c.trust_score) if c.trust_score else None, o.free_cancellation)
        for o, c in competition
    ]
    order = rank(items)["order"]
    return order.index(offer.id) + 1 if offer.id in order else None


def to_my_out(db: Session, offer: Offer) -> MyOfferOut:
    hotel_name, city_name = db.execute(
        select(Hotel.name, City.name).join(City, City.id == Hotel.city_id).where(Hotel.id == offer.hotel_id)
    ).one()
    position, total, lowest = position_of(offer, live_competition(db, offer.hotel_id, offer.room_type))
    return MyOfferOut(
        **OfferOut.model_validate(offer).model_dump(),
        hotel_name=hotel_name,
        city_name=city_name,
        position=position,
        competitors=total,
        lowest_price=lowest,
    )


def create_undercut_alerts(db: Session, offer: Offer, old_price: int | None) -> int:
    """Tells every competitor this offer has just gone below. "Just" matters: a competitor who was already
    more expensive before this change got the alert last time. Returns how many alerts were created."""
    count = 0
    for other, company in live_competition(db, offer.hotel_id, offer.room_type):
        if other.company_id == offer.company_id or other.price_per_night <= offer.price_per_night:
            continue
        if old_price is not None and old_price < other.price_per_night:
            continue  # this offer was already cheaper than theirs before
        gap = other.price_per_night - offer.price_per_night
        hotel_name = db.scalar(select(Hotel.name).where(Hotel.id == offer.hotel_id))
        db.add(
            PriceAlert(
                company_id=company.id,
                offer_id=other.id,
                type="undercut",
                message=(
                    f'A competitor now offers "{offer.room_type}" at {hotel_name} for {offer.price_per_night} EGP, '
                    f"{gap} EGP below your {other.price_per_night} EGP."
                ),
            )
        )
        count += 1
    return count


def market_median(db: Session, offer: Offer) -> int | None:
    prices = [o.price_per_night for o, _ in live_competition(db, offer.hotel_id, offer.room_type) if o.id != offer.id]
    return int(median(prices)) if prices else None


def pause_all_for_company(db: Session, company_id: int) -> int:
    """Set every active offer of this company to paused. Returns how many changed. Doesn't commit."""
    result = db.execute(
        update(Offer).where(Offer.company_id == company_id, Offer.status == "active").values(status="paused")
    )
    return result.rowcount or 0


def best_offers_for_cities(db: Session, city_ids: list[int], budget_level: str, per_city: int = 3) -> list[dict]:
    """For the trip planner: per city, each hotel's cheapest live offer, ordered by how well it fits the budget.
    low: cheapest first · mid: closest to the city's middle price · high: most stars, then best trust."""
    rows = db.execute(
        select(Offer, Company, Hotel)
        .join(Company, Company.id == Offer.company_id)
        .join(Hotel, Hotel.id == Offer.hotel_id)
        .where(Hotel.city_id.in_(city_ids), live_conditions())
        .order_by(Offer.price_per_night)
    ).all()
    cheapest_per_hotel: dict[int, tuple[Offer, Company, Hotel]] = {}
    for offer, company, hotel in rows:
        cheapest_per_hotel.setdefault(hotel.id, (offer, company, hotel))

    result: list[dict] = []
    for city_id in city_ids:
        options = [v for v in cheapest_per_hotel.values() if v[2].city_id == city_id]
        if not options:
            continue
        if budget_level == "low":
            options.sort(key=lambda v: v[0].price_per_night)
        elif budget_level == "high":
            options.sort(key=lambda v: (-(v[2].stars or 0), -float(v[1].trust_score or 0), v[0].price_per_night))
        else:
            middle = median(v[0].price_per_night for v in options)
            options.sort(key=lambda v: abs(v[0].price_per_night - middle))
        for offer, company, hotel in options[:per_city]:
            result.append(
                {
                    "offer_id": offer.id,
                    "city_id": city_id,
                    "hotel_name": hotel.name,
                    "price_per_night": offer.price_per_night,
                    "trust_score": float(company.trust_score) if company.trust_score is not None else None,
                }
            )
    return result
