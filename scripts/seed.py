"""Fill a fresh dev database with sample data.

    python -m scripts.seed

Order matters: users and companies, then cities, then places/hotels, then offers, then trips.
Each seed function must be safe to run twice (check before inserting).
"""

import app.models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.accounts import seed as accounts_seed
from app.modules.catalog import seed as catalog_seed
from app.modules.hotels import seed as hotels_seed
from app.modules.offers import seed as offers_seed
from app.modules.places import seed as places_seed
from app.modules.trips import seed as trips_seed

STEPS = [
    ("accounts + companies (Person 1)", accounts_seed.seed),
    ("cities + interests (Person 3)", catalog_seed.seed),
    ("places (Person 4)", places_seed.seed),
    ("hotels + training examples (Person 5)", hotels_seed.seed),
    ("offers (Person 6)", offers_seed.seed),
    ("sample trip (Person 2)", trips_seed.seed),
]


def main() -> None:
    with SessionLocal() as db:
        for label, step in STEPS:
            step(db)
            db.commit()
            print(f"seeded: {label}")


if __name__ == "__main__":
    main()
