"""Feature: hotels (admin CRUD and CSV import, public list and detail)."""

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.modules.companies.models import Company
from app.modules.offers.models import Offer
from tests.conftest import API, auth_header


@pytest.fixture
def admin(client):
    return auth_header(client, "hotels-admin@test.dev", role="admin")


@pytest.fixture
def city(client, admin):
    def make(name):
        res = client.post(f"{API}/admin/cities", json={"name": name}, headers=admin)
        assert res.status_code == 201, res.text
        return res.json()

    return make


def add_hotel(client, admin, **fields):
    res = client.post(f"{API}/admin/hotels", json=fields, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


def add_offer(hotel_id, price, status="active", room="Double"):
    with SessionLocal() as db:
        owner = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar_one()
        company = Company(owner_user_id=owner, name=f"Offer Co {hotel_id}-{price}-{room}", status="approved")
        db.add(company)
        db.flush()
        db.add(Offer(hotel_id=hotel_id, company_id=company.id, room_type=room, price_per_night=price, status=status))
        db.commit()


def test_hotel_crud(client, admin, city):
    luxor = city("Hotel City A")
    hotel = add_hotel(client, admin, city_id=luxor["id"], name="Nile Breeze", stars=4, amenities=["pool"])
    assert hotel["city_name"] == "Hotel City A"
    assert hotel["min_price"] is None and hotel["offers_count"] == 0

    dup = client.post(f"{API}/admin/hotels", json={"city_id": luxor["id"], "name": "nile breeze"}, headers=admin)
    assert dup.status_code == 409
    bad_city = client.post(f"{API}/admin/hotels", json={"city_id": 999999, "name": "X Hotel"}, headers=admin)
    assert bad_city.status_code == 400

    upd = client.patch(f"{API}/admin/hotels/{hotel['id']}", json={"stars": 5}, headers=admin).json()
    assert upd["stars"] == 5 and upd["amenities"] == ["pool"]

    detail = client.get(f"{API}/hotels/{hotel['id']}")  # public
    assert detail.status_code == 200 and detail.json()["name"] == "Nile Breeze"

    assert client.delete(f"{API}/admin/hotels/{hotel['id']}", headers=admin).status_code == 204
    assert client.get(f"{API}/hotels/{hotel['id']}").status_code == 404


def test_delete_blocked_by_active_offers(client, admin, city):
    c = city("Hotel City B")
    hotel = add_hotel(client, admin, city_id=c["id"], name="Busy Hotel")
    add_offer(hotel["id"], 1200)
    assert client.delete(f"{API}/admin/hotels/{hotel['id']}", headers=admin).status_code == 409


def test_public_list_prices_filters_and_sort(client, admin, city):
    c = city("Hotel City C")
    cheap = add_hotel(client, admin, city_id=c["id"], name="Cheap Stay", stars=3)
    fancy = add_hotel(client, admin, city_id=c["id"], name="Fancy Stay", stars=5)
    add_hotel(client, admin, city_id=c["id"], name="No Offers Yet", stars=4)
    add_offer(cheap["id"], 900)
    add_offer(cheap["id"], 1100, room="Single")
    add_offer(cheap["id"], 500, status="paused", room="Suite")  # paused offers don't count
    add_offer(fancy["id"], 3000)

    res = client.get(f"{API}/hotels", params={"city_id": c["id"]}).json()
    assert [h["name"] for h in res["data"]] == ["Cheap Stay", "Fancy Stay", "No Offers Yet"]  # by price, no price last
    first = res["data"][0]
    assert first["min_price"] == 900 and first["offers_count"] == 2

    under = client.get(f"{API}/hotels", params={"city_id": c["id"], "max_price": 1000}).json()
    assert [h["name"] for h in under["data"]] == ["Cheap Stay"]
    five = client.get(f"{API}/hotels", params={"city_id": c["id"], "stars": 5}).json()
    assert [h["name"] for h in five["data"]] == ["Fancy Stay"]
    by_stars = client.get(f"{API}/hotels", params={"city_id": c["id"], "sort": "stars"}).json()
    assert by_stars["data"][0]["name"] == "Fancy Stay"


def test_admin_list_and_search(client, admin, city):
    c = city("Hotel City D")
    add_hotel(client, admin, city_id=c["id"], name="Alpha Palace")
    add_hotel(client, admin, city_id=c["id"], name="Beta Inn")
    res = client.get(f"{API}/admin/hotels", params={"city_id": c["id"], "search": "PALACE"}, headers=admin).json()
    assert res["total"] == 1 and res["data"][0]["name"] == "Alpha Palace"


def test_csv_import(client, admin, city):
    city("Import City")
    good = b"city,name,stars,amenities\nImport City,Import One,4,pool;wifi\nimport city,Import Two,,\n"
    res = client.post(f"{API}/admin/hotels/import", files={"file": ("h.csv", good, "text/csv")}, headers=admin)
    assert res.status_code == 201, res.text
    assert res.json() == {"created": 2, "skipped": 0, "skipped_names": []}

    again = client.post(f"{API}/admin/hotels/import", files={"file": ("h.csv", good, "text/csv")}, headers=admin)
    assert again.json()["created"] == 0 and again.json()["skipped"] == 2

    bad = b"city,name,stars\nNowhere,X,4\nImport City,Y,9\n"
    res = client.post(f"{API}/admin/hotels/import", files={"file": ("h.csv", bad, "text/csv")}, headers=admin)
    assert res.status_code == 400
    errors = res.json()["detail"]["errors"]
    assert [e["row"] for e in errors] == [2, 3]

    no_name = b"city,stars\nImport City,3\n"
    res = client.post(f"{API}/admin/hotels/import", files={"file": ("h.csv", no_name, "text/csv")}, headers=admin)
    assert res.status_code == 400
