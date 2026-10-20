"""Feature: trip summary, save, share link and the public read-only view."""

from tests.conftest import API, auth_header
from tests.test_trips import admin, generate, me, uid, world  # pytest fixtures


def test_summary_splits_costs(client, me, world):
    trip = generate(client, me, world, budget_total=5000)
    # Add a paid meal to day 1 so "other" isn't empty
    day1 = trip["itinerary"][0]
    client.post(
        f"{API}/trips/{trip['id']}/days/{day1['id']}/items",
        json={"type": "meal", "cost": 150, "note": "Lunch"},
        headers=me,
    )

    s = client.get(f"{API}/trips/{trip['id']}/summary", headers=me).json()
    assert s["costs"] == {"hotels": 4000, "tickets": 750, "other": 150, "total": 4900}
    assert s["remaining"] == 100 and s["over_budget"] is False
    assert s["nights_with_hotel"] == 3 and s["places_count"] == 6

    alpha, beta = s["cities"]
    assert alpha["city_id"] == world["A"] and alpha["days"] == 2
    assert alpha["costs"] == {"hotels": 2000, "tickets": 600, "other": 150, "total": 2750}
    assert beta["costs"]["total"] == 2150

    first = s["hotels"][0]
    assert first["offer_id"] == world["offer_a_cheap"] and first["nights"] == 2 and first["subtotal"] == 2000
    assert first["first_night"] == "2026-11-01"
    assert [d["costs"]["total"] for d in s["per_day"]] == [1650, 1100, 2150]
    assert s["per_day"][0]["visits"] == 2 and s["is_shared"] is False


def test_over_budget_remaining_is_negative(client, me, world):
    trip = generate(client, me, world, budget_total=1000)
    s = client.get(f"{API}/trips/{trip['id']}/summary", headers=me).json()
    assert s["over_budget"] is True and s["remaining"] == 1000 - s["costs"]["total"]


def test_save_marks_trip_saved(client, me, world):
    trip = generate(client, me, world)
    saved = client.post(f"{API}/trips/{trip['id']}/save", headers=me).json()
    assert saved["status"] == "saved"
    assert client.post(f"{API}/trips/{trip['id']}/save", headers=me).status_code == 200  # saving twice is fine
    assert client.get(f"{API}/trips", headers=me).json()[0]["status"] == "saved"


def test_share_link_lifecycle(client, me, world):
    trip = generate(client, me, world, budget_total=9000)
    first = client.post(f"{API}/trips/{trip['id']}/share", headers=me).json()
    assert first["share_path"] == f"/shared/{first['share_token']}" and len(first["share_token"]) >= 20
    again = client.post(f"{API}/trips/{trip['id']}/share", headers=me).json()
    assert again == first  # same link

    public = client.get(f"{API}/shared/{first['share_token']}")  # no login
    assert public.status_code == 200
    view = public.json()
    assert view["title"] == trip["title"] and len(view["itinerary"]) == 3
    assert "budget_total" not in view and "id" not in view

    # The link shows later edits
    client.patch(f"{API}/trips/{trip['id']}", json={"title": "Family trip"}, headers=me)
    assert client.get(f"{API}/shared/{first['share_token']}").json()["title"] == "Family trip"

    assert client.delete(f"{API}/trips/{trip['id']}/share", headers=me).status_code == 204
    assert client.get(f"{API}/shared/{first['share_token']}").status_code == 404
    new = client.post(f"{API}/trips/{trip['id']}/share", headers=me).json()
    assert new["share_token"] != first["share_token"]
    assert client.get(f"{API}/trips/{trip['id']}/summary", headers=me).json()["is_shared"] is True


def test_owner_only(client, me, world):
    trip = generate(client, me, world)
    other = auth_header(client, f"share-other-{uid()}@test.dev")
    assert client.get(f"{API}/trips/{trip['id']}/summary", headers=other).status_code == 404
    assert client.post(f"{API}/trips/{trip['id']}/save", headers=other).status_code == 404
    assert client.post(f"{API}/trips/{trip['id']}/share", headers=other).status_code == 404
    assert client.delete(f"{API}/trips/{trip['id']}/share", headers=other).status_code == 404
    assert client.get(f"{API}/shared/not-a-real-token").status_code == 404
