"""Seed: a few NL-to-SQL training examples, as if an admin had fixed them. Owner: Person 5.

They show the format the AI follows: one SELECT on hotel_best_price (and offers), returning hotel_id.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ai_quality.models import TrainingExample
from app.modules.catalog.models import City


def seed(db: Session) -> None:
    city = dict(db.execute(select(City.name, City.id)).all())
    if not {"Cairo", "Luxor", "Aswan"} <= city.keys():
        return
    examples = [
        (
            "family hotel in cairo with breakfast",
            f"SELECT hotel_id, hotel_name, min_price FROM hotel_best_price WHERE city_id = {city['Cairo']} "
            "AND hotel_id IN (SELECT hotel_id FROM offers WHERE status = 'active' AND breakfast_included) "
            "ORDER BY stars DESC NULLS LAST, min_price",
        ),
        (
            "cheapest 5 star hotel in aswan",
            f"SELECT hotel_id, hotel_name, min_price FROM hotel_best_price WHERE city_id = {city['Aswan']} "
            "AND stars = 5 ORDER BY min_price LIMIT 5",
        ),
        (
            "luxor hotels where many companies compete",
            f"SELECT hotel_id, hotel_name, offers_count FROM hotel_best_price WHERE city_id = {city['Luxor']} "
            "ORDER BY offers_count DESC, min_price",
        ),
    ]
    for question, sql in examples:
        if db.scalar(select(TrainingExample.id).where(TrainingExample.question == question)) is None:
            db.add(TrainingExample(question=question, sql=sql))
