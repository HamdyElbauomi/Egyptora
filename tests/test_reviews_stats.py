"""Feature: company reviews (traveler, public, company insights) and the admin overview."""

from tests.conftest import API, auth_header
from tests.test_trips import admin, generate, make_company, me, uid, world  # pytest fixtures


def company_id(client, headers):
    return client.get(f"{API}/company/me", headers=headers).json()["id"]


def review(client, headers, cid, **body):
    return client.post(f"{API}/companies/{cid}/reviews", json=body, headers=headers)


def test_only_booked_travelers_review_once(client, me, world):
    trip = generate(client, me, world)  # low budget: every night is with company one
    co1, co2 = company_id(client, world["co1"]), company_id(client, world["co2"])

    added = review(client, me, co1, rating=5, comment="Great guide, very friendly")
    assert added.status_code == 201, added.text
    added = added.json()
    assert added["review"]["sentiment"] == "positive" and added["review"]["reviewer_name"] == "Test"
    # initial score 3.7 from the checklist (google 4.0, 5 years, social 4); (10*3.7 + 5) / 11 = 3.8
    assert added["reviews_count"] == 1 and added["trust_score"] == 3.8

    assert review(client, me, co1, rating=4).status_code == 409  # same trip again
    assert review(client, me, co2, rating=1, comment="bad").status_code == 403  # never booked them
    other_trip = generate(client, auth_header(client, f"rv-{uid()}@test.dev"), world)
    assert review(client, me, co1, rating=3, trip_id=other_trip["id"]).status_code == 403  # not my trip
    assert review(client, world["co1"], co1, rating=5).status_code == 403  # companies can't review

    public = client.get(f"{API}/companies/{co1}/reviews").json()
    assert public["total"] == 1 and public["data"][0]["comment"] == "Great guide, very friendly"
    assert client.get(f"{API}/companies/{co1}").json()["trust_score"] == 3.8
    assert trip["id"]


def test_company_insights(client, me, world):
    co1 = company_id(client, world["co1"])
    generate(client, me, world)
    review(client, me, co1, rating=5, comment="Amazing trip, the hotel was clean")
    second = auth_header(client, f"rv2-{uid()}@test.dev")
    generate(client, second, world)
    review(client, second, co1, rating=2, comment="Bus was late and the room was dirty")
    third = auth_header(client, f"rv3-{uid()}@test.dev")
    generate(client, third, world)
    review(client, third, co1, rating=4)  # no comment -> no sentiment

    mine = client.get(f"{API}/company/reviews", headers=world["co1"]).json()
    assert mine["total"] == 3 and mine["data"][0]["sentiment"] is None

    insights = client.get(f"{API}/company/reviews/insights", headers=world["co1"]).json()
    assert insights["reviews_count"] == 3 and insights["average_rating"] == round(11 / 3, 2)
    assert insights["rating_counts"] == {"1": 0, "2": 1, "3": 0, "4": 1, "5": 1}
    assert insights["sentiment_counts"] == {"positive": 1, "neutral": 0, "negative": 1}
    assert insights["positive_share"] == 0.5
    assert insights["top_complaints"][:2] == ["late pickup or delays", "cleanliness"]
    assert [r["rating"] for r in insights["recent_negative"]] == [2]
    assert client.get(f"{API}/company/reviews/insights", headers=me).status_code == 403


def test_unapproved_company_has_no_public_reviews(client, admin):
    form = {
        "owner_name": "Owner",
        "email": f"pending-{uid()}@reviews.dev",
        "password": "password123",
        "company_name": f"Pending Reviews {uid()}",
        "license_no": "ETA-9",
    }
    res = client.post(
        f"{API}/company/register", data=form, files={"license_file": ("l.pdf", b"%PDF", "application/pdf")}
    )
    cid = res.json()["company"]["id"]
    assert client.get(f"{API}/companies/{cid}/reviews").status_code == 404
    traveler = auth_header(client, f"rv4-{uid()}@test.dev")
    assert review(client, traveler, cid, rating=5).status_code == 404


def test_admin_overview(client, admin, me, world):
    trip = generate(client, me, world)
    client.post(f"{API}/trips/{trip['id']}/share", headers=me)
    make_company(client, admin, f"Approved {uid()}")
    form = {
        "owner_name": "Owner",
        "email": f"waiting-{uid()}@stats.dev",
        "password": "password123",
        "company_name": f"Waiting {uid()}",
        "license_no": "ETA-2",
    }
    client.post(f"{API}/company/register", data=form, files={"license_file": ("l.pdf", b"%PDF", "application/pdf")})

    s = client.get(f"{API}/admin/stats", headers=admin)
    assert s.status_code == 200, s.text
    s = s.json()
    assert set(s) == {"users", "trips", "companies", "offers", "catalog", "reviews", "ai", "needs_attention"}
    assert s["users"]["travelers"] >= 1 and s["users"]["admins"] >= 1
    assert s["trips"]["total"] >= 1 and s["trips"]["shared"] >= 1 and s["trips"]["avg_days"] is not None
    assert s["companies"]["pending"] >= 1 and s["needs_attention"]["pending_companies"] == s["companies"]["pending"]
    assert s["offers"]["active"] >= 4 and s["offers"]["nights_booked_in_trips"] >= 3
    assert s["catalog"]["hotels"] >= 3
    assert client.get(f"{API}/admin/stats", headers=me).status_code == 403
