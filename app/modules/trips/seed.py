"""Seed: one sample trip for traveler1@egyptora.dev. Owner: Person 2.

4 days in Cairo and Luxor, mid budget, ancient history + museums, starting a month from today.
Built with the same generate_trip() the app uses, so it shows real places and the seeded hotel offers.
It is shared at /shared/sample, which the Welcome screen's "See a sample trip" button opens.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models import User
from app.modules.catalog.models import City, Interest
from app.modules.trips.models import Trip
from app.modules.trips.schemas import GenerateTripIn
from app.modules.trips.service import generate_trip

SAMPLE_SHARE_TOKEN = "sample"


def seed(db: Session) -> None:
    user = db.scalar(select(User).where(User.email == "traveler1@egyptora.dev"))
    if user is None:
        return
    existing = db.scalar(select(Trip).where(Trip.user_id == user.id).order_by(Trip.id))
    if existing is not None:
        share_sample(db, existing)
        return
    interests = list(db.scalars(select(Interest.id).where(Interest.name.in_(["Ancient history", "Museums"]))))
    cities = {c.name: c.id for c in db.scalars(select(City).where(City.name.in_(["Cairo", "Luxor"])))}
    if not interests or len(cities) < 2:
        return
    body = GenerateTripIn(
        interest_ids=interests,
        budget_level="mid",
        budget_total=15000,
        days=4,
        start_date=date.today() + timedelta(days=30),
        city_ids=[cities["Cairo"], cities["Luxor"]],
    )
    share_sample(db, generate_trip(db, user, body))


def share_sample(db: Session, trip: Trip) -> None:
    """Gives the sample trip its fixed public link, unless another trip already uses it."""
    if trip.share_token is None and db.scalar(select(Trip.id).where(Trip.share_token == SAMPLE_SHARE_TOKEN)) is None:
        trip.share_token = SAMPLE_SHARE_TOKEN
