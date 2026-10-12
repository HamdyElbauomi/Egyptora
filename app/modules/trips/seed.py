"""Seed: one sample trip for traveler1@egyptora.dev. Owner: Person 2.

4 days in Cairo and Luxor, mid budget, ancient history + museums, starting a month from today.
Built with the same generate_trip() the app uses, so it shows real places and the seeded hotel offers.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models import User
from app.modules.catalog.models import City, Interest
from app.modules.trips.models import Trip
from app.modules.trips.schemas import GenerateTripIn
from app.modules.trips.service import generate_trip


def seed(db: Session) -> None:
    user = db.scalar(select(User).where(User.email == "traveler1@egyptora.dev"))
    if user is None or db.scalar(select(Trip.id).where(Trip.user_id == user.id)):
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
    generate_trip(db, user, body)
