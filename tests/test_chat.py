"""Feature: chat that edits the trip (propose, Keep, Undo, safety checks)."""

from app.ai.chat_agent import ChatOut, DayAfter, ItemAfter, ProposedChange
from tests.conftest import API, auth_header
from tests.test_trips import admin, generate, me, uid, world  # pytest fixtures


def say(client, headers, trip_id, text):
    res = client.post(f"{API}/trips/{trip_id}/messages", json={"content": text}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["reply"]


def test_hotel_change_keep_and_undo(client, me, world):
    trip = generate(client, me, world)
    reply = say(client, me, trip["id"], f"better hotel in Alpha {world['tag']}")
    change = reply["change"]
    assert change["status"] == "proposed" and change["day_numbers"] == [1, 2]
    assert change["cost_delta"] == 2 * (4000 - 1000)
    # Nothing changes before Keep
    assert client.get(f"{API}/trips/{trip['id']}", headers=me).json()["total_cost"] == trip["total_cost"]

    kept = client.post(f"{API}/trip-changes/{change['id']}/keep", headers=me).json()
    assert kept["change"]["status"] == "kept"
    assert kept["trip"]["itinerary"][0]["hotel"]["offer_id"] == world["offer_a5"]
    assert kept["trip"]["itinerary"][2]["hotel"]["offer_id"] == world["offer_b"]  # other city untouched
    assert kept["trip"]["total_cost"] == trip["total_cost"] + 6000
    assert client.post(f"{API}/trip-changes/{change['id']}/keep", headers=me).status_code == 409

    undone = client.post(f"{API}/trip-changes/{change['id']}/undo", headers=me).json()
    assert undone["change"]["status"] == "undone"
    assert undone["trip"]["total_cost"] == trip["total_cost"]
    assert undone["trip"]["itinerary"][0]["hotel"]["offer_id"] == world["offer_a_cheap"]
    assert client.post(f"{API}/trip-changes/{change['id']}/undo", headers=me).status_code == 409


def test_arabic_cheaper_hotel_when_already_cheapest(client, me, world):
    trip = generate(client, me, world)
    reply = say(client, me, trip["id"], "عايز فندق أرخص")
    assert reply["change"] is None and "cheapest" in reply["content"]


def test_lighter_day_and_stale_keep(client, me, world):
    trip = generate(client, me, world)
    day1 = trip["itinerary"][0]
    change = say(client, me, trip["id"], "make day 1 lighter")["change"]
    assert change["summary"] == f"Day 1: removed Temple Two {world['tag']}" and change["cost_delta"] == -300

    # The traveler edits day 1 by hand before pressing Keep -> the suggestion is stale
    client.delete(f"{API}/trip-items/{day1['items'][0]['id']}", headers=me)
    assert client.post(f"{API}/trip-changes/{change['id']}/keep", headers=me).status_code == 409


def test_add_and_remove_place(client, me, admin, world):
    trip = generate(client, me, world)
    client.post(
        f"{API}/admin/places",
        json={"city_id": world["B"], "name": f"Tomb Two {world['tag']}", "type": "monument", "ticket_price": 80},
        headers=admin,
    )
    added = say(client, me, trip["id"], f"add tomb two {world['tag']}")["change"]
    assert added["day_numbers"] == [3] and added["cost_delta"] == 80
    after = client.post(f"{API}/trip-changes/{added['id']}/keep", headers=me).json()["trip"]
    names = [i["place_name"] for i in after["itinerary"][2]["items"]]
    assert names[-1] == f"Tomb Two {world['tag']}"
    assert after["itinerary"][2]["items"][-1]["start_time"] > after["itinerary"][2]["items"][-2]["end_time"]

    removed = say(client, me, trip["id"], f"remove market {world['tag']}")["change"]
    assert removed["day_numbers"] == [3]
    after = client.post(f"{API}/trip-changes/{removed['id']}/keep", headers=me).json()["trip"]
    assert f"Market {world['tag']}" not in [i["place_name"] for i in after["itinerary"][2]["items"]]


def test_dismiss_history_and_owner_only(client, me, world):
    trip = generate(client, me, world)
    assert say(client, me, trip["id"], "hello")["change"] is None
    change = say(client, me, trip["id"], "make day 3 lighter")["change"]
    dismissed = client.post(f"{API}/trip-changes/{change['id']}/undo", headers=me).json()
    assert dismissed["change"]["status"] == "undone" and dismissed["trip"]["total_cost"] == trip["total_cost"]

    history = client.get(f"{API}/trips/{trip['id']}/messages", headers=me).json()
    assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]
    assert history[0]["content"] == "hello" and history[3]["change"]["status"] == "undone"

    other = auth_header(client, f"chat-other-{uid()}@test.dev")
    assert client.get(f"{API}/trips/{trip['id']}/messages", headers=other).status_code == 404
    assert client.post(f"{API}/trips/{trip['id']}/messages", json={"content": "x"}, headers=other).status_code == 404
    assert client.post(f"{API}/trip-changes/{change['id']}/keep", headers=other).status_code == 404


def test_unsafe_agent_change_is_dropped(client, me, world, monkeypatch):
    """Whatever the AI says, a place from another city (or a repeated place) never gets into the trip."""
    trip = generate(client, me, world)
    day1 = trip["itinerary"][0]

    def bad_agent(body):
        return ChatOut(
            reply="Done!",
            change=ProposedChange(
                summary="Add a far place",
                explanation="",
                days=[DayAfter(day_id=day1["id"], offer_id=None, items=[ItemAfter(place_id=world["b1"])])],
            ),
        )

    monkeypatch.setattr("app.modules.chat.router.chat", bad_agent)
    reply = say(client, me, trip["id"], "anything")
    assert reply["change"] is None and "couldn't prepare that change safely" in reply["content"]
