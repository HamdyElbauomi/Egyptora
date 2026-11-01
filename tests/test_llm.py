"""The language model path (USE_LLM=true) with a fake model API, and its fallbacks to the rules."""

import json

import httpx
import pytest

from app.ai import llm
from app.ai.nl2sql import CityRef, NL2SQLIn, to_sql
from app.ai.place_qa import NOT_COVERED, AskIn, ask
from app.core.config import settings
from tests.conftest import API
from tests.test_trips import admin, generate, me, world  # pytest fixtures


class FakeModel:
    """Stands in for httpx.post: answers with the next queued reply, and remembers what it was sent."""

    def __init__(self):
        self.replies: list = []
        self.sent: list[dict] = []

    def __call__(self, url, headers=None, json=None, timeout=None):  # noqa: A002
        self.sent.append(json)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, int):
            return httpx.Response(reply, json={"error": "nope"})
        content = reply if isinstance(reply, str) else globals()["json"].dumps(reply)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


@pytest.fixture
def model(monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(settings, "use_llm", True)
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(llm.httpx, "post", fake)
    return fake


def test_parse_json_object():
    assert llm.parse_json_object('{"a": 1}') == {"a": 1}
    assert llm.parse_json_object('```json\n{"a": 2}\n```') == {"a": 2}
    assert llm.parse_json_object('Sure! {"a": 3} hope it helps') == {"a": 3}
    with pytest.raises(llm.LLMError):
        llm.parse_json_object("no json here")


NOTES = "Karnak was built over about 2,000 years. Its Hypostyle Hall has 134 columns."


def test_place_qa_uses_the_model_and_falls_back(model):
    q = AskIn(question="How many columns?", place_name="Karnak", verified_info=NOTES)
    model.replies = [{"answer": "The Hypostyle Hall has 134 columns.", "grounded": True}]
    assert ask(q).answer == "The Hypostyle Hall has 134 columns."
    assert NOTES in model.sent[0]["messages"][1]["content"]  # only the verified notes are the context

    model.replies = [{"answer": "It has a gift shop.", "grounded": False}]
    assert ask(q).answer == NOT_COVERED.format(name="Karnak")

    model.replies = [httpx.ConnectTimeout("slow"), 429]
    assert ask(q).grounded is True  # the sentence matcher answered
    assert ask(q).grounded is True


def test_search_sql_from_the_model_is_checked(model):
    body = NL2SQLIn(question="quiet 4-star in Luxor", cities=[CityRef(id=2, name="Luxor")])
    good = "SELECT hotel_id, hotel_name FROM hotel_best_price WHERE city_id = 2 AND stars = 4 LIMIT 20"
    model.replies = [{"sql": good + ";", "understood": "4-star hotels in Luxor"}]
    out = to_sql(body)
    assert out.sql == good and out.understood == "4-star hotels in Luxor"

    model.replies = [{"sql": "DELETE FROM offers", "understood": "x"}]
    assert to_sql(body).sql.startswith("SELECT hotel_id, hotel_name, stars, min_price")  # the rules answered

    model.replies = [{"sql": "SELECT hotel_name FROM hotel_best_price", "understood": "x"}]
    assert "hotel_id" in to_sql(body).sql  # no hotel_id column -> the rules answered

    # a question the admin already fixed never goes to the model
    fixed = NL2SQLIn(
        question="Fixed one", examples=[{"question": "fixed one", "sql": "SELECT hotel_id FROM hotel_best_price"}]
    )
    assert to_sql(fixed).sql == "SELECT hotel_id FROM hotel_best_price" and len(model.sent) == 3


def test_chat_action_from_the_model(client, me, world, model):
    trip = generate(client, me, world, city_ids=[world["A"]], days=2)
    current = trip["itinerary"][0]["hotel"]["offer_id"]
    other = world["offer_a5"] if current != world["offer_a5"] else world["offer_a_other"]
    model.replies = [
        {
            "reply": "عندك فندق أحسن: Alpha Palace. دوس Keep لو عاجبك.",
            "action": {"type": "set_hotel", "offer_id": other, "day_numbers": [1, 2]},
            "summary": "Switch to Alpha Palace",
            "explanation": "More stars for both nights.",
        }
    ]
    res = client.post(f"{API}/trips/{trip['id']}/messages", json={"content": "عايز فندق أحسن"}, headers=me)
    assert res.status_code == 201, res.text
    reply = res.json()["reply"]
    assert reply["content"].startswith("عندك فندق أحسن") and reply["change"]["summary"] == "Switch to Alpha Palace"
    assert reply["change"]["day_numbers"] == [1, 2] and reply["change"]["cost_delta"] != 0
    sent = json.loads(model.sent[0]["messages"][1]["content"])
    assert sent["message"] == "عايز فندق أحسن" and any(o["offer_id"] == other for o in sent["hotel_offers"])


def test_chat_falls_back_when_the_model_invents_ids(client, me, world, model):
    trip = generate(client, me, world, city_ids=[world["A"]], days=2)
    model.replies = [{"reply": "Removed it.", "action": {"type": "remove_place", "place_id": 999999}}]
    res = client.post(f"{API}/trips/{trip['id']}/messages", json={"content": "make day 1 lighter"}, headers=me)
    assert res.status_code == 201, res.text
    assert res.json()["reply"]["content"].startswith("I removed")  # the rules agent's answer
