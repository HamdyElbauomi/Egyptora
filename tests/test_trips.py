"""Feature: build the trip (generate, regenerate) and view/edit it (days, items, reorder, hotel offer)."""

import uuid

import pytest

from tests.conftest import API, auth_header

PDF = b"%PDF-1.4 license"


def uid() -> str:
    return uuid.uuid4().hex[:6]


@pytest.fixture
def admin(client):
    return auth_header(client, "trips-admin@test.dev", role="admin")


@pytest.fixture
def me(client):
    return auth_header(client, f"trav-{uid()}@test.dev")


def make_company(client, admin, name):
    form = {
        "owner_name": "Owner",
        "email": f"{name.lower().replace(' ', '')}@trips.dev",
        "password": "password123",
        "company_name": name,
        "license_no": "ETA-1",
    }
    res = client.post(f"{API}/company/register", data=form, files={"license_file": ("l.pdf", PDF, "application/pdf")})
    assert res.status_code == 201, res.text
    checklist = {"license_verified": True, "google_rating": 4.0, "years_active": 5, "social_presence": 4}
    client.post(f"{API}/admin/companies/{res.json()['company']['id']}/approve", json=checklist, headers=admin)
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def make_offer(client, headers, hotel_id, price):
    body = {"hotel_id": hotel_id, "room_type": "Double", "price_per_night": price}
    res = client.post(f"{API}/company/offers", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.fixture
def world(client, admin):
    """Two cities, two interests, places, hotels and offers, all with unique names."""
    tag = uid()
    post = lambda path, body: client.post(f"{API}{path}", json=body, headers=admin).json()  # noqa: E731
    w = {"tag": tag}
    w["history"] = post("/admin/interests", {"name": f"History {tag}"})["id"]
    w["food"] = post("/admin/interests", {"name": f"Food {tag}"})["id"]
    w["A"] = post("/admin/cities", {"name": f"Alpha {tag}"})["id"]
    w["B"] = post("/admin/cities", {"name": f"Beta {tag}"})["id"]

    def place(city, name, minutes, ticket, interests):
        body = {
            "city_id": w[city],
            "name": f"{name} {tag}",
            "type": "monument",
            "visit_minutes": minutes,
            "ticket_price": ticket,
            "interest_ids": [w[i] for i in interests],
        }
        return post("/admin/places", body)["id"]

    w["a1"] = place("A", "Temple One", 120, 200, ["history"])
    w["a2"] = place("A", "Temple Two", 180, 300, ["history"])
    w["a3"] = place("A", "Food Street", 60, 0, ["food"])
    w["a4"] = place("A", "Temple Four", 240, 100, ["history"])
    w["b1"] = place("B", "Tomb One", 90, 150, ["history"])
    w["b2"] = place("B", "Market", 90, 0, ["food"])

    w["hotel_a"] = post("/admin/hotels", {"city_id": w["A"], "name": f"Alpha Inn {tag}", "stars": 3})["id"]
    w["hotel_a5"] = post("/admin/hotels", {"city_id": w["A"], "name": f"Alpha Palace {tag}", "stars": 5})["id"]
    w["hotel_b"] = post("/admin/hotels", {"city_id": w["B"], "name": f"Beta Lodge {tag}", "stars": 4})["id"]
    w["co1"] = make_company(client, admin, f"Trip Co One {tag}")
    w["co2"] = make_company(client, admin, f"Trip Co Two {tag}")
    w["offer_a_cheap"] = make_offer(client, w["co1"], w["hotel_a"], 1000)
    w["offer_a_other"] = make_offer(client, w["co2"], w["hotel_a"], 1100)
    w["offer_a5"] = make_offer(client, w["co1"], w["hotel_a5"], 4000)
    w["offer_b"] = make_offer(client, w["co1"], w["hotel_b"], 2000)
    return w


def generate(client, headers, world, **extra):
    body = {
        "interest_ids": [world["history"]],
        "budget_level": "low",
        "days": 3,
        "city_ids": [world["A"], world["B"]],
        "start_date": "2026-11-01",
        **extra,
    }
    res = client.post(f"{API}/trips/generate", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_generate_full_trip(client, me, world):
    trip = generate(client, me, world)
    tag = world["tag"]
    assert trip["title"] == f"3 days in Alpha {tag} & Beta {tag}"
    assert trip["status"] == "draft" and trip["end_date"] == "2026-11-03"
    assert [c["id"] for c in trip["cities"]] == [world["A"], world["B"]]
    days = trip["itinerary"]
    assert [d["city_id"] for d in days] == [world["A"], world["A"], world["B"]]
    assert [d["date"] for d in days] == ["2026-11-01", "2026-11-02", "2026-11-03"]

    # Matching places first, every place once, days start at 09:00
    placed = [i["place_id"] for d in days for i in d["items"]]
    assert sorted(placed) == sorted(world[k] for k in ("a1", "a2", "a3", "a4", "b1", "b2"))
    assert days[0]["items"][0]["place_id"] == world["a1"]
    assert days[0]["items"][0]["start_time"] == "09:00:00" and days[0]["items"][0]["end_time"] == "11:00:00"
    assert days[0]["items"][1]["start_time"] == "11:30:00"
    assert days[0]["items"][0]["place_name"] == f"Temple One {tag}"

    # Low budget -> cheapest hotel in each city, same hotel for the whole stay
    assert days[0]["hotel"]["offer_id"] == world["offer_a_cheap"] == days[1]["hotel"]["offer_id"]
    assert days[2]["hotel"]["hotel_name"] == f"Beta Lodge {tag}"
    assert trip["total_cost"] == sum(d["day_cost"] for d in days) == 200 + 300 + 100 + 150 + 1000 * 2 + 2000
    assert trip["over_budget"] is False

    assert client.get(f"{API}/trips/{trip['id']}", headers=me).json() == trip


def test_generate_validation(client, me, admin, world):
    def gen(**body):
        base = {"interest_ids": [world["history"]], "budget_level": "mid", "days": 2, "city_ids": [world["A"]]}
        return client.post(f"{API}/trips/generate", json={**base, **body}, headers=me)

    assert gen(city_ids=[999999]).status_code == 400
    assert gen(interest_ids=[999999]).status_code == 400
    assert gen(days=1, city_ids=[world["A"], world["B"]]).status_code == 400
    assert gen(city_ids=[]).status_code == 422  # no cities and suggest=false
    assert gen(budget_level="cheap").status_code == 422
    assert client.post(f"{API}/trips/generate", json={}, headers=admin).status_code == 403
    assert client.post(f"{API}/trips/generate", json={}).status_code == 401


def test_suggest_picks_the_matching_city(client, me, admin, world):
    only_beta = client.post(f"{API}/admin/interests", json={"name": f"Tombs {world['tag']}"}, headers=admin).json()
    client.patch(f"{API}/admin/places/{world['b1']}", json={"interest_ids": [only_beta["id"]]}, headers=admin)
    trip = generate(client, me, world, interest_ids=[only_beta["id"]], city_ids=[], suggest=True, days=2)
    assert [c["id"] for c in trip["cities"]] == [world["B"]]
    assert trip["itinerary"][0]["items"][0]["place_id"] == world["b1"]


def test_budget_total_controls_hotel(client, me, world):
    luxury = generate(client, me, world, budget_level="high", city_ids=[world["A"]], days=2)
    assert luxury["itinerary"][0]["hotel"]["offer_id"] == world["offer_a5"]  # 5 stars

    capped = generate(client, me, world, budget_level="high", city_ids=[world["A"]], days=2, budget_total=3000)
    assert capped["itinerary"][0]["hotel"]["offer_id"] == world["offer_a_cheap"]  # 4000/night doesn't fit

    tiny = generate(client, me, world, city_ids=[world["A"]], days=2, budget_total=100)
    assert tiny["over_budget"] is True


def test_owner_only_list_and_delete(client, me, world):
    mine = generate(client, me, world)
    other = auth_header(client, f"other-{uid()}@test.dev")
    assert client.get(f"{API}/trips/{mine['id']}", headers=other).status_code == 404
    assert client.get(f"{API}/trips", headers=other).json() == []
    cards = client.get(f"{API}/trips", headers=me).json()
    assert cards[0]["id"] == mine["id"] and cards[0]["cities"] == [c["name"] for c in mine["cities"]]
    assert client.delete(f"{API}/trips/{mine['id']}", headers=other).status_code == 404
    assert client.delete(f"{API}/trips/{mine['id']}", headers=me).status_code == 204
    assert client.get(f"{API}/trips/{mine['id']}", headers=me).status_code == 404


def test_items_add_edit_reorder_delete(client, me, admin, world):
    trip = generate(client, me, world)
    day1 = trip["itinerary"][0]
    url = f"{API}/trips/{trip['id']}/days/{day1['id']}/items"

    assert client.post(url, json={"place_id": world["b1"]}, headers=me).status_code == 400  # other city
    assert client.post(url, json={"place_id": world["a4"]}, headers=me).status_code == 409  # already in trip
    assert client.post(url, json={"type": "visit"}, headers=me).status_code == 422  # visit needs a place

    new_place = client.post(
        f"{API}/admin/places",
        json={
            "city_id": world["A"],
            "name": f"Museum {world['tag']}",
            "type": "museum",
            "visit_minutes": 60,
            "ticket_price": 250,
        },
        headers=admin,
    ).json()
    after = client.post(url, json={"place_id": new_place["id"]}, headers=me)
    assert after.status_code == 201, after.text
    after = after.json()
    added = after["itinerary"][0]["items"][-1]
    last_before = day1["items"][-1]
    assert added["place_id"] == new_place["id"] and added["cost"] == 250
    assert added["start_time"] > last_before["end_time"]  # after the last item (+30 min)
    assert after["total_cost"] == trip["total_cost"] + 250

    edited = client.patch(f"{API}/trip-items/{added['id']}", json={"cost": 50, "note": "Student ticket"}, headers=me)
    assert edited.json()["total_cost"] == trip["total_cost"] + 50
    bad = client.patch(f"{API}/trip-items/{added['id']}", json={"start_time": "18:00", "end_time": "17:00"}, headers=me)
    assert bad.status_code == 422

    ids = [i["id"] for i in after["itinerary"][0]["items"]]
    order_url = f"{API}/trips/{trip['id']}/days/{day1['id']}/order"
    assert client.put(order_url, json={"item_ids": ids[:-1]}, headers=me).status_code == 400
    reordered = client.put(order_url, json={"item_ids": list(reversed(ids))}, headers=me).json()
    items = reordered["itinerary"][0]["items"]
    assert [i["id"] for i in items] == list(reversed(ids))
    assert items[0]["start_time"] == "09:00:00" and items[0]["end_time"] == "10:00:00"  # 60-min museum first

    other = auth_header(client, f"intruder-{uid()}@test.dev")
    assert client.delete(f"{API}/trip-items/{added['id']}", headers=other).status_code == 404
    assert client.delete(f"{API}/trip-items/{added['id']}", headers=me).status_code == 204
    assert client.get(f"{API}/trips/{trip['id']}", headers=me).json()["total_cost"] == trip["total_cost"]


def test_choose_offer_for_a_night(client, me, world):
    trip = generate(client, me, world)
    day1 = trip["itinerary"][0]
    url = f"{API}/trips/{trip['id']}/days/{day1['id']}/offer"

    picked = client.put(url, json={"offer_id": world["offer_a_other"]}, headers=me).json()
    assert picked["itinerary"][0]["hotel"]["price_per_night"] == 1100
    assert picked["total_cost"] == trip["total_cost"] + 100

    assert client.put(url, json={"offer_id": world["offer_b"]}, headers=me).status_code == 400  # other city
    client.post(f"{API}/company/offers/{world['offer_a5']}/pause", headers=world["co1"])
    assert client.put(url, json={"offer_id": world["offer_a5"]}, headers=me).status_code == 400  # paused

    cleared = client.put(url, json={"offer_id": None}, headers=me).json()
    assert cleared["itinerary"][0]["hotel"] is None
    assert cleared["total_cost"] == trip["total_cost"] - 1000


def test_regenerate_and_change_days(client, me, world):
    trip = generate(client, me, world)
    again = client.post(f"{API}/trips/{trip['id']}/regenerate", headers=me)
    assert again.status_code == 200
    again = again.json()
    assert again["id"] == trip["id"] and again["title"] == trip["title"] and len(again["itinerary"]) == 3
    placed = [i["place_id"] for d in again["itinerary"] for i in d["items"] if i["place_id"]]
    assert len(placed) == len(set(placed)) == 6

    url = f"{API}/trips/{trip['id']}"
    shorter = client.patch(url, json={"days": 2, "title": "Short trip"}, headers=me).json()
    assert shorter["days"] == 2 and len(shorter["itinerary"]) == 2 and shorter["title"] == "Short trip"
    assert shorter["end_date"] == "2026-11-02"
    longer = client.patch(url, json={"days": 4}, headers=me).json()
    assert [d["day_number"] for d in longer["itinerary"]] == [1, 2, 3, 4]
    assert longer["itinerary"][3]["items"] == [] and longer["itinerary"][3]["city_id"] == world["A"]
    assert client.patch(url, json={"days": 0}, headers=me).status_code == 422


def test_city_places_for_add_dialog(client, world):
    places = client.get(f"{API}/cities/{world['B']}/places")  # public, no login
    assert places.status_code == 200
    body = places.json()
    assert [p["id"] for p in body] == [world["b2"], world["b1"]]  # by name: Market, Tomb One
    assert body[1]["ticket_price"] == 150 and body[1]["interest_ids"] == [world["history"]]
    assert client.get(f"{API}/cities/999999/places").status_code == 404
