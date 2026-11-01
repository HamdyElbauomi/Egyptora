"""Seed: cities and interest chips. Owner: Person 3."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City, Interest

CITIES = [
    ("Cairo", "Pyramids, Islamic Cairo and the Egyptian Museum.", 30.0444, 31.2357),
    ("Luxor", "Karnak, Luxor Temple and the Valley of the Kings.", 25.6872, 32.6396),
    ("Aswan", "Philae, the Nubian villages and the Nile at its calmest.", 24.0889, 32.8998),
]

INTERESTS = [
    ("Ancient history", "history", "Temples, tombs and the pyramids"),
    ("Museums", "image", "Treasures, mummies and old masters"),
    ("Food", "food", "Street food, cooking and bazaars"),
    ("Nile and nature", "leaf", "Felucca rides, gardens and islands"),
    ("Markets and shopping", "briefcase", "Souks, crafts and spices"),
    ("Nightlife", "moon", "Rooftops and evening Nile cruises"),
    ("Religious sites", "pin", "Mosques, churches and old quarters"),
    ("Photography", "camera", "Viewpoints and golden hours"),
]


def seed(db: Session) -> None:
    for name, desc, lat, lng in CITIES:
        if db.scalar(select(City).where(City.name == name)) is None:
            db.add(City(name=name, description=desc, lat=lat, lng=lng))
    for name, icon, description in INTERESTS:
        if db.scalar(select(Interest).where(Interest.name == name)) is None:
            db.add(Interest(name=name, icon=icon, description=description))
