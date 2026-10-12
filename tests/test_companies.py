"""Feature: companies and trust (sign-up, profile, admin review, public profile)."""

import pytest

from app.core.database import SessionLocal
from app.modules.companies.models import Review
from app.modules.offers.models import Offer
from tests.conftest import API, auth_header

PDF = b"%PDF-1.4 test license"


@pytest.fixture
def admin(client):
    return auth_header(client, "companies-admin@test.dev", role="admin")


def register(client, name, email, file=("license.pdf", PDF, "application/pdf")):
    form = {
        "owner_name": "Owner",
        "email": email,
        "password": "password123",
        "company_name": name,
        "license_no": "ETA-12345",
    }
    return client.post(f"{API}/company/register", data=form, files={"license_file": file})


def company_headers(res):
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def checklist(**overrides):
    return {"license_verified": True, "google_rating": 4.4, "years_active": 8, "social_presence": 4, **overrides}


def test_register_creates_pending_company_and_logs_in(client):
    res = register(client, "Lotus Nile Tours", "lotus@test.dev")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["role"] == "company"
    assert body["company"]["status"] == "pending"
    assert body["company"]["license_doc_url"].startswith("/uploads/companies/")
    assert client.get(body["company"]["license_doc_url"]).status_code == 200

    me = client.get(f"{API}/company/me", headers=company_headers(res)).json()
    assert me["name"] == "Lotus Nile Tours"


def test_register_validation(client):
    register(client, "Dup Name Co", "dup1@test.dev")
    assert register(client, "Another Co", "dup1@test.dev").status_code == 409  # same email
    assert register(client, "dup name co", "dup2@test.dev").status_code == 409  # same name, any case
    assert register(client, "Bad File Co", "bad@test.dev", ("a.txt", b"hi", "text/plain")).status_code == 400
    assert register(client, "Bad Email Co", "not-an-email").status_code == 422


def test_portal_needs_company_role(client):
    traveler = auth_header(client, "portal-traveler@test.dev")
    assert client.get(f"{API}/company/me", headers=traveler).status_code == 403


def test_update_profile_and_reupload_license_after_reject(client, admin):
    res = register(client, "Red Sea Trips", "redsea@test.dev")
    headers = company_headers(res)
    company_id = res.json()["company"]["id"]

    upd = client.patch(f"{API}/company/me", json={"website": "https://redsea.example"}, headers=headers)
    assert upd.json()["website"] == "https://redsea.example/"
    assert upd.json()["phone"] is None

    rej = client.post(f"{API}/admin/companies/{company_id}/reject", json={"reason": "License is blurry"}, headers=admin)
    assert rej.json()["status"] == "rejected"
    assert client.get(f"{API}/company/me", headers=headers).json()["reject_reason"] == "License is blurry"

    new = client.post(
        f"{API}/company/me/documents", files={"file": ("new.pdf", PDF, "application/pdf")}, headers=headers
    )
    assert new.status_code == 200
    assert new.json()["status"] == "pending"
    assert new.json()["reject_reason"] is None


def test_admin_queue_lists_pending_first(client, admin):
    register(client, "Queue Co A", "qa@test.dev")
    page = client.get(f"{API}/admin/companies", params={"status": "pending"}, headers=admin).json()
    assert page["total"] >= 1
    assert all(c["status"] == "pending" for c in page["data"])
    first = client.get(f"{API}/admin/companies", headers=admin).json()["data"][0]
    assert first["status"] == "pending"


def test_approve_sets_trust_and_public_profile(client, admin):
    res = register(client, "Karnak Gate Travel", "karnakgate@test.dev")
    company_id = res.json()["company"]["id"]
    assert client.get(f"{API}/companies/{company_id}").status_code == 404  # pending is not public

    bad = client.post(
        f"{API}/admin/companies/{company_id}/approve", json=checklist(license_verified=False), headers=admin
    )
    assert bad.status_code == 400

    ok = client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist(), headers=admin)
    assert ok.status_code == 200, ok.text
    assert ok.json()["initial_score"] == 4.2
    assert ok.json()["trust_score"] == 4.2
    assert ok.json()["company"]["status"] == "approved"

    public = client.get(f"{API}/companies/{company_id}").json()
    assert public["trust_score"] == 4.2 and public["years_active"] == 8

    again = client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist(), headers=admin)
    assert again.status_code == 409  # already approved
    assert (
        client.post(f"{API}/admin/companies/{company_id}/reject", json={"reason": "too late now"}, headers=admin)
    ).status_code == 409  # only pending can be rejected


def test_trust_blends_reviews(client, admin):
    res = register(client, "Blend Co", "blend@test.dev")
    company_id = res.json()["company"]["id"]
    owner_id = client.get(f"{API}/admin/companies/{company_id}", headers=admin).json()["owner_user_id"]
    with SessionLocal() as db:  # 38 reviews averaging 4.3, like the example in trust.py
        for i in range(38):
            db.add(Review(company_id=company_id, user_id=owner_id, trip_id=None, rating=5 if i < 26 else 3))
        db.commit()
    ok = client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist(), headers=admin).json()
    # (10 × 4.2 + 38 × 4.37) ÷ 48 = 4.33 -> 4.3
    assert ok["trust_score"] == 4.3
    assert ok["company"]["reviews_count"] == 38


def test_suspend_pauses_offers_and_reapprove(client, admin):
    res = register(client, "Suspend Co", "suspend@test.dev")
    company_id = res.json()["company"]["id"]
    client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist(), headers=admin)

    cairo = client.post(f"{API}/admin/cities", json={"name": "Suspend City"}, headers=admin).json()
    from app.modules.hotels.models import Hotel

    with SessionLocal() as db:
        hotel = Hotel(city_id=cairo["id"], name="Suspend Hotel", stars=4)
        db.add(hotel)
        db.flush()
        db.add_all(
            [
                Offer(hotel_id=hotel.id, company_id=company_id, room_type="Double", price_per_night=1500),
                Offer(hotel_id=hotel.id, company_id=company_id, room_type="Single", price_per_night=1100),
            ]
        )
        db.commit()

    sus = client.post(f"{API}/admin/companies/{company_id}/suspend", headers=admin)
    assert sus.status_code == 200
    assert sus.json()["paused_offers"] == 2
    assert sus.json()["company"]["active_offers"] == 0
    assert client.get(f"{API}/companies/{company_id}").status_code == 404

    back = client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist(), headers=admin)
    assert back.json()["company"]["status"] == "approved"


def test_analyze_reviews(client, admin):
    res = register(client, "Analyze Co", "analyze@test.dev")
    company_id = res.json()["company"]["id"]
    out = client.post(
        f"{API}/admin/companies/{company_id}/analyze-reviews",
        json={"reviews": ["Great guide", "Bus was late"]},
        headers=admin,
    ).json()
    assert len(out["items"]) == 2
    assert 0 <= out["suggested_social_presence"] <= 5
