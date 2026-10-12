"""Feature: offers and competition (company offers, market, alerts, admin flags, public comparison)."""

import pytest

from tests.conftest import API, auth_header

PDF = b"%PDF-1.4 license"


@pytest.fixture
def admin(client):
    return auth_header(client, "offers-admin@test.dev", role="admin")


@pytest.fixture
def hotel(client, admin):
    def make(name, stars=4):
        city = client.post(f"{API}/admin/cities", json={"name": f"{name} City"}, headers=admin).json()
        res = client.post(
            f"{API}/admin/hotels", json={"city_id": city["id"], "name": name, "stars": stars}, headers=admin
        )
        assert res.status_code == 201, res.text
        return res.json()

    return make


@pytest.fixture
def company(client, admin):
    """Registers a company and approves it. Returns (headers, company_id)."""

    def make(name, approve=True, social=4):
        form = {
            "owner_name": "Owner",
            "email": f"{name.lower().replace(' ', '')}@offers.dev",
            "password": "password123",
            "company_name": name,
            "license_no": "ETA-1",
        }
        res = client.post(
            f"{API}/company/register", data=form, files={"license_file": ("l.pdf", PDF, "application/pdf")}
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
        company_id = res.json()["company"]["id"]
        if approve:
            checklist = {"license_verified": True, "google_rating": 4.0, "years_active": 5, "social_presence": social}
            client.post(f"{API}/admin/companies/{company_id}/approve", json=checklist, headers=admin)
        return headers, company_id

    return make


def offer(client, headers, hotel_id, price, **extra):
    body = {"hotel_id": hotel_id, "room_type": "Double", "price_per_night": price, **extra}
    res = client.post(f"{API}/company/offers", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_only_approved_companies_sell(client, hotel, company):
    h = hotel("Gate One")
    pending, _ = company("Pending Seller", approve=False)
    res = client.post(
        f"{API}/company/offers",
        json={"hotel_id": h["id"], "room_type": "Double", "price_per_night": 1000},
        headers=pending,
    )
    assert res.status_code == 403
    assert client.get(f"{API}/company/dashboard", headers=pending).json()["status"] == "pending"


def test_create_validation(client, hotel, company):
    h = hotel("Gate Two")
    seller, _ = company("Valid Seller")
    offer(client, seller, h["id"], 1000)
    dup = client.post(
        f"{API}/company/offers",
        json={"hotel_id": h["id"], "room_type": "double", "price_per_night": 900},
        headers=seller,
    )
    assert dup.status_code == 409
    bad_hotel = client.post(
        f"{API}/company/offers", json={"hotel_id": 999999, "room_type": "Double", "price_per_night": 9}, headers=seller
    )
    assert bad_hotel.status_code == 400
    bad_dates = client.post(
        f"{API}/company/offers",
        json={
            "hotel_id": h["id"],
            "room_type": "Suite",
            "price_per_night": 9,
            "valid_from": "2026-12-10",
            "valid_to": "2026-12-01",
        },
        headers=seller,
    )
    assert bad_dates.status_code == 422


def test_market_position_and_undercut_alerts(client, hotel, company):
    h = hotel("Karnak Test Inn", stars=3)
    a, _ = company("Seller A")
    b, _ = company("Seller B")
    c, _ = company("Seller C")
    offer(client, a, h["id"], 1350)
    ob = offer(client, b, h["id"], 1280)  # undercuts A -> alert for A
    oc = offer(client, c, h["id"], 1450)  # most expensive -> no alerts
    assert oc["position"] == 3 and oc["competitors"] == 3 and oc["lowest_price"] == 1280

    a_alerts = client.get(f"{API}/company/alerts", headers=a).json()
    assert len(a_alerts) == 1 and a_alerts[0]["type"] == "undercut" and "1280" in a_alerts[0]["message"]
    assert client.get(f"{API}/company/alerts", headers=c).json() == []

    # C drops to 1200: now cheapest -> alerts for A and B (both were cheaper than C before)
    client.patch(f"{API}/company/offers/{oc['id']}", json={"price_per_night": 1200}, headers=c)
    assert len(client.get(f"{API}/company/alerts", headers=b).json()) == 1
    assert len(client.get(f"{API}/company/alerts", headers=a).json()) == 2

    market = client.get(f"{API}/company/offers/{ob['id']}/market", headers=b).json()
    assert market["position"] == 2 and market["total"] == 3
    assert market["lowest_price"] == 1200 and market["gap_to_lowest"] == 80
    assert [x["is_mine"] for x in market["competitors"]] == [False, True, False]

    dash = client.get(f"{API}/company/dashboard", headers=c).json()
    assert dash["active_offers"] == 1 and dash["cheapest_in_market"] == 1

    alert_id = a_alerts[0]["id"]
    assert client.post(f"{API}/company/alerts/{alert_id}/read", headers=a).json()["is_read"] is True
    assert client.post(f"{API}/company/alerts/{alert_id}/read", headers=b).status_code == 404  # not B's


def test_pause_resume_delete_and_ownership(client, hotel, company):
    h = hotel("Gate Three")
    seller, _ = company("Pause Seller")
    other, _ = company("Other Seller")
    o = offer(client, seller, h["id"], 2000)
    assert client.post(f"{API}/company/offers/{o['id']}/pause", headers=other).status_code == 404
    paused = client.post(f"{API}/company/offers/{o['id']}/pause", headers=seller).json()
    assert paused["status"] == "paused" and paused["position"] is None
    assert client.post(f"{API}/company/offers/{o['id']}/pause", headers=seller).status_code == 409
    assert client.get(f"{API}/hotels/{h['id']}").json()["offers_count"] == 0
    assert client.post(f"{API}/company/offers/{o['id']}/resume", headers=seller).json()["status"] == "active"
    assert client.delete(f"{API}/company/offers/{o['id']}", headers=seller).status_code == 204
    assert client.get(f"{API}/company/offers", headers=seller).json() == []


def test_public_comparison_badges(client, hotel, company):
    h = hotel("Badge Hotel", stars=3)
    cheap, _ = company("Cheap Low Trust", social=0)
    trusted, _ = company("Trusted Seller", social=5)
    paused_seller, _ = company("Paused Seller")
    offer(client, cheap, h["id"], 1200)
    offer(client, trusted, h["id"], 1250, free_cancellation=True, cancellation_days=3)
    p = offer(client, paused_seller, h["id"], 900)
    client.post(f"{API}/company/offers/{p['id']}/pause", headers=paused_seller)

    res = client.get(f"{API}/hotels/{h['id']}/offers").json()  # public, best value first
    names = [x["company"]["name"] for x in res["offers"]]
    assert names == ["Trusted Seller", "Cheap Low Trust"]  # paused offer hidden
    assert res["offers"][0]["is_best_value"] and not res["offers"][0]["is_lowest"]
    assert res["offers"][1]["is_lowest"]
    lowest_first = client.get(f"{API}/hotels/{h['id']}/offers", params={"sort": "lowest"}).json()
    assert [x["price_per_night"] for x in lowest_first["offers"]] == [1200, 1250]


def test_admin_flag_hides_and_alerts(client, admin, hotel, company):
    h = hotel("Flag Hotel")
    a, _ = company("Normal One")
    b, _ = company("Normal Two")
    s, _ = company("Too Cheap")
    offer(client, a, h["id"], 2000)
    offer(client, b, h["id"], 2200)
    bad = offer(client, s, h["id"], 300)

    listing = client.get(f"{API}/admin/offers", params={"hotel_id": h["id"]}, headers=admin).json()
    checks = {o["company_name"]: o["price_check"] for o in listing["data"]}
    assert checks == {"Too Cheap": "low", "Normal One": None, "Normal Two": None}

    flagged = client.post(
        f"{API}/admin/offers/{bad['id']}/flag", json={"reason": "Price looks like a typo"}, headers=admin
    )
    assert flagged.json()["status"] == "flagged"
    assert len(client.get(f"{API}/hotels/{h['id']}/offers").json()["offers"]) == 2
    alerts = client.get(f"{API}/company/alerts", headers=s).json()
    assert any(x["type"] == "price_anomaly" and "typo" in x["message"] for x in alerts)
    assert client.post(f"{API}/company/offers/{bad['id']}/resume", headers=s).status_code == 409

    assert client.post(f"{API}/admin/offers/{bad['id']}/unflag", headers=admin).json()["status"] == "active"


def test_suspended_company_offers_disappear(client, admin, hotel, company):
    h = hotel("Suspend Hotel Two")
    seller, company_id = company("Soon Suspended")
    offer(client, seller, h["id"], 1500)
    client.post(f"{API}/admin/companies/{company_id}/suspend", headers=admin)
    assert client.get(f"{API}/hotels/{h['id']}/offers").json()["offers"] == []


def test_csv_import_creates_and_updates(client, hotel, company):
    h = hotel("Import Offer Hotel")
    seller, _ = company("Csv Seller")
    csv1 = (
        f"hotel_id,room_type,price_per_night,free_cancellation\n{h['id']},Double,1500,yes\n{h['id']},Single,1100,no\n"
    )
    res = client.post(
        f"{API}/company/offers/import", files={"file": ("o.csv", csv1.encode(), "text/csv")}, headers=seller
    )
    assert res.status_code == 201, res.text
    assert res.json() == {"created": 2, "updated": 0}
    csv2 = f"hotel_id,room_type,price_per_night\n{h['id']},double,1400\n"
    res = client.post(
        f"{API}/company/offers/import", files={"file": ("o.csv", csv2.encode(), "text/csv")}, headers=seller
    )
    assert res.json() == {"created": 0, "updated": 1}
    bad = "hotel_id,room_type,price_per_night\n999999,Double,1000\nabc,Double,1\n"
    res = client.post(
        f"{API}/company/offers/import", files={"file": ("o.csv", bad.encode(), "text/csv")}, headers=seller
    )
    assert res.status_code == 400 and len(res.json()["detail"]["errors"]) == 2
