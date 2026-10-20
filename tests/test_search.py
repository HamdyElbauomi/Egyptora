"""Feature: plain-language hotel search, its SQL safety, and the admin AI-quality screen."""

import pytest

from app.ai.nl2sql import NL2SQLOut
from app.modules.ai_quality.service import UnsafeSQL, check_sql
from tests.conftest import API, auth_header
from tests.test_trips import admin, generate, me, uid, world  # pytest fixtures


def search(client, headers, question, **extra):
    res = client.post(f"{API}/hotels/search", json={"question": question, **extra}, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def names(result):
    return [h["name"] for h in result["results"]]


def test_search_understands_filters(client, me, world):
    tag = world["tag"]
    three = search(client, me, f"3-star in alpha {tag} under 1050")
    assert names(three) == [f"Alpha Inn {tag}"] and three["count"] == 1 and not three["fallback"]
    assert three["understood"] == f"3-star hotels in Alpha {tag} under 1050 EGP/night"
    assert three["results"][0]["min_price"] == 1000

    arabic = search(client, me, f"فندق 5 نجوم في alpha {tag}")
    assert names(arabic) == [f"Alpha Palace {tag}"]
    luxury = search(client, me, f"luxury hotel in alpha {tag}")
    assert names(luxury) == [f"Alpha Palace {tag}", f"Alpha Inn {tag}"]


def test_free_cancellation_and_no_results(client, admin, me, world):
    tag = world["tag"]
    body = {"hotel_id": world["hotel_b"], "room_type": "Suite", "price_per_night": 2500, "free_cancellation": True}
    assert client.post(f"{API}/company/offers", json=body, headers=world["co2"]).status_code == 201

    beta = search(client, me, f"beta {tag} with free cancellation")
    assert names(beta) == [f"Beta Lodge {tag}"]
    none = search(client, me, f"alpha {tag} with free cancellation")
    assert none["results"] == [] and not none["fallback"] and "No hotels match" in none["message"]

    flagged = client.get(f"{API}/admin/ai/queries", params={"status": "flagged", "limit": 100}, headers=admin).json()
    assert none["query_id"] in [q["id"] for q in flagged["data"]]


def test_trip_city_is_used(client, me, world):
    trip = generate(client, me, world, city_ids=[world["B"]], days=1)
    result = search(client, me, "cheapest hotel", trip_id=trip["id"])
    assert result["results"] and {h["city_id"] for h in result["results"]} == {world["B"]}
    other = auth_header(client, f"search-other-{uid()}@test.dev")
    res = client.post(f"{API}/hotels/search", json={"question": "cheapest", "trip_id": trip["id"]}, headers=other)
    assert res.status_code == 404
    assert client.post(f"{API}/hotels/search", json={"question": "cheapest"}).status_code == 401


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM offers",
        "SELECT * FROM hotel_best_price; DROP TABLE users",
        "SELECT * FROM users",
        "SELECT pg_sleep(10) FROM hotel_best_price",
        "SELECT * FROM hotel_best_price -- hi",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "SELECT * INTO copy FROM offers",
        "SELECT * FROM hotel_best_price JOIN users ON true",
        "SELECT * FROM information_schema.tables",
    ],
)
def test_unsafe_sql_is_refused(sql):
    with pytest.raises(UnsafeSQL):
        check_sql(sql)


def test_safe_sql_passes():
    sql = (
        "SELECT hotel_id FROM hotel_best_price WHERE hotel_id IN (SELECT hotel_id FROM offers WHERE free_cancellation);"
    )
    assert check_sql(sql) == sql.rstrip(";")


def test_failed_search_fix_and_train(client, admin, me, world, monkeypatch):
    tag = world["tag"]
    question = f"rooms with a view of alpha {tag}"
    monkeypatch.setattr(
        "app.modules.ai_quality.service.to_sql", lambda body: NL2SQLOut(sql="DROP TABLE hotels", understood=None)
    )
    failed = search(client, me, question)
    assert failed["fallback"] is True and failed["results"] == []
    monkeypatch.undo()

    queue = client.get(f"{API}/admin/ai/queries", params={"limit": 100}, headers=admin).json()  # failed by default
    logged = next(q for q in queue["data"] if q["id"] == failed["query_id"])
    assert logged["status"] == "failed" and "only SELECT" in logged["error"] and logged["generated_sql"]

    qid = failed["query_id"]
    url = f"{API}/admin/ai/queries/{qid}"
    assert client.post(f"{url}/add-to-training", headers=admin).status_code == 409  # not fixed yet
    assert client.post(f"{url}/fix", json={"sql": "DELETE FROM offers"}, headers=admin).status_code == 400
    assert client.post(f"{url}/fix", json={"sql": "SELECT id FROM hotels"}, headers=admin).status_code == 400
    no_id = client.post(f"{url}/fix", json={"sql": "SELECT hotel_name FROM hotel_best_price"}, headers=admin)
    assert no_id.status_code == 400 and "hotel_id" in no_id.json()["detail"]

    good_sql = f"SELECT hotel_id FROM hotel_best_price WHERE city_id = {world['A']} AND stars = 5"
    fixed = client.post(f"{url}/fix", json={"sql": good_sql}, headers=admin).json()
    assert fixed["result_count"] == 1 and fixed["preview"][0]["hotel_name"] == f"Alpha Palace {tag}"
    assert fixed["query"]["fixed_sql"] == good_sql and fixed["query"]["reviewed_by"] is not None

    example = client.post(f"{url}/add-to-training", headers=admin)
    assert example.status_code == 201 and example.json()["source_query_id"] == qid
    assert client.post(f"{url}/add-to-training", headers=admin).status_code == 409

    # The same question now uses the admin's SQL
    again = search(client, me, question)
    assert names(again) == [f"Alpha Palace {tag}"] and again["understood"] == "A search our team checked by hand"

    examples = client.get(f"{API}/admin/ai/training-examples", headers=admin).json()
    assert examples[0]["id"] == example.json()["id"]
    assert client.delete(f"{API}/admin/ai/training-examples/{examples[0]['id']}", headers=admin).status_code == 204
    assert client.delete(f"{API}/admin/ai/training-examples/{examples[0]['id']}", headers=admin).status_code == 404


def test_metrics(client, admin, me, world):
    search(client, me, f"hotels in alpha {world['tag']}")
    m = client.get(f"{API}/admin/ai/metrics", headers=admin).json()
    assert m["search"]["total"] >= 1 and m["search"]["ok"] >= 1
    assert 0 <= m["search"]["success_rate"] <= 1 and m["search"]["p95_latency_ms"] is not None
    assert set(m) == {"search", "scans", "chat", "training"}
    assert m["scans"]["threshold"] == 0.6
    assert client.get(f"{API}/admin/ai/metrics", headers=me).status_code == 403
