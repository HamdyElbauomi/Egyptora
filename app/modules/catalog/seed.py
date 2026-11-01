"""Seed: cities and interest chips, as in the Figma design. Owner: Person 3.

9 cities and 8 interests. Older dev databases (seeded with Cairo/Luxor/Aswan and the first 8 interests)
are brought up to date in place: renamed, merged, and given the design's icons and descriptions,
so `python -m scripts.seed` is enough after pulling.
"""

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.catalog.models import City, Interest
from app.modules.places.models import PlaceInterest
from app.modules.trips.models import TripInterest

# name, description (shown on the destination card), lat, lng
CITIES = [
    ("Cairo & Giza", "Pyramids, museums, old city", 30.0444, 31.2357),
    ("Luxor", "Temples and royal tombs", 25.6872, 32.6396),
    ("Aswan", "Nubian culture, Philae", 24.0889, 32.8998),
    ("Alexandria", "Mediterranean city", 31.2001, 29.9187),
    ("Hurghada", "Red Sea diving", 27.2579, 33.8116),
    ("Sharm El-Sheikh", "Reefs and resorts", 27.9158, 34.3300),
    ("Dahab", "Laid-back Sinai coast", 28.5091, 34.5136),
    ("Siwa Oasis", "Western Desert", 29.2032, 25.5195),
    ("Fayoum", "Lakes and desert near Cairo", 29.3084, 30.8428),
]

# name, icon (from the design's icon set), description
INTERESTS = [
    ("History & monuments", "history", "Temples, tombs, museums"),
    ("Adventure", "mountain", "Desert safaris, diving, hikes"),
    ("Food & markets", "food", "Street food, cooking, bazaars"),
    ("Calm & slow", "leaf", "Quiet spots, gardens, rest days"),
    ("Sea & beaches", "waves", "Red Sea and Mediterranean coast"),
    ("Art & culture", "music", "Galleries, crafts, live music"),
    ("Photography", "camera", "Viewpoints and golden hours"),
    ("Nights out", "moon", "Rooftops, evening Nile cruises"),
]

# Earlier seed names -> design names. In order: a rename when the new name is free, a merge when it exists.
OLD_CITIES = {"Cairo": "Cairo & Giza"}
OLD_INTERESTS = [
    ("Ancient history", "History & monuments"),
    ("Museums", "History & monuments"),
    ("Religious sites", "History & monuments"),
    ("Food", "Food & markets"),
    ("Markets and shopping", "Food & markets"),
    ("Nile and nature", "Calm & slow"),
    ("Nightlife", "Nights out"),
]


def merge_interest(db: Session, old: Interest, into: Interest) -> None:
    """Moves place and trip links from `old` to `into` (skipping ones already there), then deletes `old`."""
    for model, owner in ((PlaceInterest, PlaceInterest.place_id), (TripInterest, TripInterest.trip_id)):
        has_new = select(owner).where(model.interest_id == into.id)
        db.execute(update(model).where(model.interest_id == old.id, owner.not_in(has_new)).values(interest_id=into.id))
        db.execute(delete(model).where(model.interest_id == old.id))
    db.delete(old)
    db.flush()


def upgrade_old_names(db: Session) -> None:
    for old, new in OLD_CITIES.items():
        city = db.scalar(select(City).where(City.name == old))
        if city is not None and db.scalar(select(City.id).where(City.name == new)) is None:
            city.name = new
            db.flush()
    for old, new in OLD_INTERESTS:
        interest = db.scalar(select(Interest).where(Interest.name == old))
        if interest is None:
            continue
        target = db.scalar(select(Interest).where(Interest.name == new))
        if target is None:
            interest.name = new
            db.flush()  # sessions don't autoflush: the next lookup must see the new name
        else:
            merge_interest(db, interest, target)


def seed(db: Session) -> None:
    upgrade_old_names(db)
    for name, desc, lat, lng in CITIES:
        city = db.scalar(select(City).where(City.name == name))
        if city is None:
            db.add(City(name=name, description=desc, lat=lat, lng=lng))
        else:
            city.description = desc
    for name, icon, description in INTERESTS:
        interest = db.scalar(select(Interest).where(Interest.name == name))
        if interest is None:
            db.add(Interest(name=name, icon=icon, description=description))
        else:
            interest.icon, interest.description = icon, description
