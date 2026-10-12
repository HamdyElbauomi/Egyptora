"""Seed: competing offers from the 4 seeded companies on the seeded hotels.

Prices are sample values that follow the star rating, with each company a little cheaper or pricier,
so Lowest / Best value / market position have something to compare. Karnak Gate Inn matches the design:
Sunrise 1,200 · Blue Lotus 1,280 · Nile Horizon 1,350 · Pharaoh Path 1,450.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.companies.models import Company
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer

BASE_BY_STARS = {2: 700, 3: 1200, 4: 2200, 5: 4500}

# company name: (price multiplier, free cancellation, breakfast, skips every Nth hotel)
COMPANIES = {
    "Sunrise Travel": (1.00, False, False, None),
    "Blue Lotus Tours": (1.067, True, True, 4),
    "Nile Horizon": (1.125, True, True, 3),
    "Pharaoh Path": (1.208, False, True, 2),
}


def seed(db: Session) -> None:
    companies = {c.name: c for c in db.scalars(select(Company).where(Company.name.in_(COMPANIES)))}
    hotels = list(db.scalars(select(Hotel).order_by(Hotel.id)))
    for index, hotel in enumerate(hotels):
        base = BASE_BY_STARS.get(hotel.stars or 3, 1200)
        for name, (multiplier, free_cancel, breakfast, skip_every) in COMPANIES.items():
            company = companies.get(name)
            if company is None or (skip_every and index % skip_every == skip_every - 1):
                continue
            exists = db.scalar(
                select(Offer.id).where(
                    Offer.hotel_id == hotel.id, Offer.company_id == company.id, Offer.room_type == "Double"
                )
            )
            if exists:
                continue
            db.add(
                Offer(
                    hotel_id=hotel.id,
                    company_id=company.id,
                    room_type="Double",
                    price_per_night=int(round(base * multiplier, -1)),
                    free_cancellation=free_cancel,
                    cancellation_days=3 if free_cancel else None,
                    breakfast_included=breakfast,
                )
            )
