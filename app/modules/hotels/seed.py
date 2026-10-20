"""Seed: sample hotels for Cairo, Luxor and Aswan.

The names are fictional on purpose: this is demo data, and real hotel names would come with star ratings
and details we can't verify. The admin adds or imports the real list (see scripts/data/hotels_sample.csv
for the CSV format). NL-to-SQL training examples are seeded in ai_quality/seed.py.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City
from app.modules.hotels.models import Hotel

HOTELS = [
    # city, name, stars, address, lat, lng, amenities, description
    (
        "Cairo",
        "Giza Plateau View Hotel",
        4,
        "Al Haram, Giza",
        29.9850,
        31.1450,
        ["pyramids view", "pool", "wifi", "breakfast"],
        "Rooftop terrace facing the pyramids.",
    ),
    (
        "Cairo",
        "Tahrir Gardens Inn",
        3,
        "Downtown Cairo",
        30.0450,
        31.2370,
        ["wifi", "breakfast"],
        "Simple rooms a short walk from the Egyptian Museum.",
    ),
    (
        "Cairo",
        "Zamalek Nile Residence",
        5,
        "Zamalek, Cairo",
        30.0610,
        31.2190,
        ["nile view", "pool", "spa", "gym", "wifi"],
        "Riverside hotel on Gezira Island.",
    ),
    (
        "Cairo",
        "Al-Muizz Courtyard House",
        3,
        "Islamic Cairo",
        30.0500,
        31.2610,
        ["wifi", "breakfast", "rooftop"],
        "Small guesthouse near Khan el-Khalili.",
    ),
    (
        "Luxor",
        "Karnak Gate Inn",
        3,
        "Karnak, East Bank",
        25.7150,
        32.6520,
        ["wifi", "breakfast", "garden"],
        "Walking distance to Karnak Temple.",
    ),
    (
        "Luxor",
        "Theban Palms Hotel",
        4,
        "Corniche El Nile, Luxor",
        25.6990,
        32.6380,
        ["nile view", "pool", "wifi", "breakfast"],
        "On the corniche between Luxor and Karnak temples.",
    ),
    (
        "Luxor",
        "West Bank Mud-Brick Lodge",
        3,
        "Al Bairat, West Bank",
        25.7230,
        32.6050,
        ["garden", "breakfast", "bicycle rental"],
        "Quiet lodge close to the Valley of the Kings.",
    ),
    (
        "Luxor",
        "Luxor Royal Nile Resort",
        5,
        "Khaled Ibn El Walid St, Luxor",
        25.6880,
        32.6420,
        ["nile view", "pool", "spa", "gym", "wifi"],
        "Large resort with gardens on the Nile.",
    ),
    (
        "Aswan",
        "Cataract Sunset Hotel",
        5,
        "Abtal El Tahrir St, Aswan",
        24.0820,
        32.8880,
        ["nile view", "pool", "spa", "wifi"],
        "Terraces over the Nile's first cataract.",
    ),
    (
        "Aswan",
        "Elephantine Nubian Guesthouse",
        3,
        "Elephantine Island",
        24.0880,
        32.8860,
        ["nile view", "breakfast", "wifi"],
        "Colorful Nubian-style rooms on the island.",
    ),
    (
        "Aswan",
        "Aswan Corniche Hotel",
        4,
        "Corniche El Nile, Aswan",
        24.0940,
        32.8990,
        ["nile view", "pool", "wifi", "breakfast"],
        "Central hotel facing the Nile.",
    ),
    (
        "Aswan",
        "Philae Garden Hotel",
        3,
        "Sadat Rd, Aswan",
        24.0780,
        32.8950,
        ["garden", "wifi", "breakfast"],
        "Budget-friendly rooms near the Unfinished Obelisk.",
    ),
]


def seed(db: Session) -> None:
    cities = {c.name: c.id for c in db.scalars(select(City))}
    for city, name, stars, address, lat, lng, amenities, description in HOTELS:
        if city not in cities:
            continue
        if db.scalar(select(Hotel.id).where(Hotel.name == name, Hotel.city_id == cities[city])):
            continue
        db.add(
            Hotel(
                city_id=cities[city],
                name=name,
                stars=stars,
                address=address,
                lat=lat,
                lng=lng,
                amenities=amenities,
                description=description,
            )
        )
