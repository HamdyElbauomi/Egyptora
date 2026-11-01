"""The design's catalog: joined city names ("Cairo & Giza") and upgrading old dev seed names."""

import uuid

from sqlalchemy import select

from app.ai.cities import mentions_city, name_parts
from app.ai.nl2sql import CityRef, NL2SQLIn, rules_sql
from app.modules.catalog.models import City, Interest
from app.modules.catalog.seed import upgrade_old_names
from app.modules.places.models import Place, PlaceInterest
from tests.conftest import API
from tests.test_trips import admin, me, world  # pytest fixtures


def test_city_names_match_by_any_part():
    assert name_parts("Cairo & Giza") == ["cairo & giza", "cairo", "giza"]
    assert mentions_city("Cairo & Giza", "cheap hotel in giza")
    assert mentions_city("Cairo & Giza", "فندق في القاهرة")
    assert mentions_city("Siwa Oasis", "lodge in siwa")
    assert mentions_city("Sharm El-Sheikh", "resort in sharm")
    assert not mentions_city("Luxor", "hotel in aswan")


def test_search_understands_a_joined_city_name():
    cities = [CityRef(id=1, name="Cairo & Giza"), CityRef(id=2, name="Luxor")]
    out = rules_sql(NL2SQLIn(question="4-star hotel in Giza", cities=cities))
    assert "city_id = 1" in out.sql and "in Cairo & Giza" in (out.understood or "")


def test_trip_title_with_a_joined_city_name(client, admin, me, world):
    tag = uuid.uuid4().hex[:6]
    city = client.post(f"{API}/admin/cities", json={"name": f"Sun & Sand {tag}"}, headers=admin).json()
    body = {"interest_ids": [world["history"]], "budget_level": "mid", "days": 2, "city_ids": [world["A"], city["id"]]}
    trip = client.post(f"{API}/trips/generate", json=body, headers=me)
    assert trip.status_code == 201, trip.text
    assert trip.json()["title"] == f"2 days in Alpha {world['tag']}, Sun & Sand {tag}"


def test_old_seed_interests_are_renamed_and_merged(db):
    # an old dev database: "Ancient history" and "Museums", one place tagged with both
    if db.scalar(select(Interest.id).where(Interest.name.in_(["Ancient history", "History & monuments"]))):
        return  # another run already upgraded this database
    old = Interest(name="Ancient history", icon="pyramid")
    museums = Interest(name="Museums", icon="museum")
    db.add_all([old, museums])
    db.flush()
    city = City(name=f"Old City {uuid.uuid4().hex[:6]}")
    db.add(city)
    db.flush()
    place = Place(city_id=city.id, name=f"Old Temple {uuid.uuid4().hex[:6]}", type="monument")
    db.add(place)
    db.flush()
    db.add_all(
        [PlaceInterest(place_id=place.id, interest_id=old.id), PlaceInterest(place_id=place.id, interest_id=museums.id)]
    )
    db.flush()

    upgrade_old_names(db)
    upgrade_old_names(db)  # safe to run twice
    db.commit()

    names = set(db.scalars(select(Interest.name)))
    assert "History & monuments" in names and not names & {"Ancient history", "Museums"}
    tags = list(db.scalars(select(PlaceInterest.interest_id).where(PlaceInterest.place_id == place.id)))
    assert tags == [old.id]  # renamed in place, the duplicate link merged away
