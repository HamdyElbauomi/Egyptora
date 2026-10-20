"""Feature: scan a monument, ask about it, admin review queue and labeling."""

import uuid

import pytest

from tests.conftest import API, auth_header


def photo(label: str = "", confidence: float = 0.9) -> tuple:
    """A fake JPEG that the mock recognizer reads as <label> with <confidence>."""
    return ("photo.jpg", f"\xff\xd8 egyptora-mock:{label}:{confidence}".encode(), "image/jpeg")


@pytest.fixture
def admin(client):
    return auth_header(client, "scans-admin@test.dev", role="admin")


@pytest.fixture
def traveler(client):
    return auth_header(client, f"scanner-{uuid.uuid4().hex[:6]}@test.dev")


@pytest.fixture
def monument(client, admin):
    tag = uuid.uuid4().hex[:6]
    city = client.post(f"{API}/admin/cities", json={"name": f"Scan City {tag}"}, headers=admin).json()
    body = {
        "city_id": city["id"],
        "name": f"Temple of Tests {tag}",
        "type": "monument",
        "recognition_label": f"temple_{tag}",
        "source_url": "https://example.org/temple",
        "verified_info": (
            "The temple was built by Ramesses II around 1250 BC. "
            "Its facade has four colossal statues of the king. "
            "It was moved in the 1960s to save it from the rising lake."
        ),
    }
    place = client.post(f"{API}/admin/places", json=body, headers=admin)
    assert place.status_code == 201, place.text
    return place.json()


def scan(client, headers, label="", confidence=0.9):
    res = client.post(f"{API}/scans", files={"photo": photo(label, confidence)}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_recognized_scan_returns_verified_place(client, traveler, monument):
    out = scan(client, traveler, monument["recognition_label"], 0.93)
    assert out["status"] == "recognized" and out["confidence"] == 0.93
    assert out["place"]["id"] == monument["id"] and "Ramesses II" in out["place"]["verified_info"]
    assert out["place"]["city_name"].startswith("Scan City")
    assert out["image_url"].startswith("/uploads/scans/")


def test_not_sure_paths(client, traveler, monument):
    low = scan(client, traveler, monument["recognition_label"], 0.4)
    assert low["status"] == "not_sure" and low["place"] is None
    unknown = scan(client, traveler, "no_such_monument", 0.99)
    assert unknown["status"] == "not_sure"
    bad = client.post(f"{API}/scans", files={"photo": ("x.gif", b"GIF89a", "image/gif")}, headers=traveler)
    assert bad.status_code == 400


def test_my_scans_are_private_and_newest_first(client, traveler, monument):
    first = scan(client, traveler, monument["recognition_label"], 0.95)
    second = scan(client, traveler, "", 0.2)
    mine = client.get(f"{API}/scans", headers=traveler).json()
    assert [s["id"] for s in mine["data"]] == [second["scan_id"], first["scan_id"]]
    assert mine["data"][1]["place_name"] == monument["name"] and mine["data"][0]["place_id"] is None
    other = auth_header(client, f"other-scanner-{uuid.uuid4().hex[:6]}@test.dev")
    assert client.get(f"{API}/scans", headers=other).json()["total"] == 0


def test_admin_labels_unsure_scan(client, admin, traveler, monument):
    unsure = scan(client, traveler, monument["recognition_label"], 0.35)
    queue = client.get(f"{API}/admin/ai/scans", headers=admin, params={"limit": 100}).json()
    assert unsure["scan_id"] in [s["id"] for s in queue["data"]]

    labeled = client.post(
        f"{API}/admin/ai/scans/{unsure['scan_id']}/label", json={"place_id": monument["id"]}, headers=admin
    )
    assert labeled.status_code == 200, labeled.text
    labeled = labeled.json()
    assert labeled["scan"]["labeled"] and labeled["scan"]["place_id"] == monument["id"]
    image = labeled["training_image"]
    assert image["source"] == "user_scan" and image["used_for_training"]
    assert image["image_url"].startswith(f"/uploads/places/{monument['id']}/")

    queue = client.get(f"{API}/admin/ai/scans", headers=admin, params={"limit": 100}).json()
    assert unsure["scan_id"] not in [s["id"] for s in queue["data"]]
    everything = client.get(
        f"{API}/admin/ai/scans", headers=admin, params={"max_confidence": 1, "only_unlabeled": False, "limit": 100}
    ).json()
    assert unsure["scan_id"] in [s["id"] for s in everything["data"]]

    # The traveler now sees the place; the public page doesn't show the traveler's photo
    assert client.get(f"{API}/scans", headers=traveler).json()["data"][0]["place_id"] == monument["id"]
    assert client.get(f"{API}/places/{monument['id']}").json()["images"] == []

    assert client.post(f"{API}/admin/ai/scans/999999/label", json={"place_id": 1}, headers=admin).status_code == 404
    assert client.get(f"{API}/admin/ai/scans", headers=traveler).status_code == 403


def test_ask_answers_only_from_verified_info(client, admin, traveler, monument):
    url = f"{API}/places/{monument['id']}/ask"
    built = client.post(url, json={"question": "Who built it?"}, headers=traveler).json()
    assert built["grounded"] and "Ramesses II" in built["answer"] and built["source_url"]
    moved = client.post(url, json={"question": "Why was it moved?"}, headers=traveler).json()
    assert moved["grounded"] and "1960s" in moved["answer"]
    unknown = client.post(url, json={"question": "Is there parking nearby?"}, headers=traveler).json()
    assert unknown == {
        "answer": f"Our verified notes about {monument['name']} don't cover that yet.",
        "grounded": False,
        "source_url": None,
    }

    bare = client.post(
        f"{API}/admin/places",
        json={"city_id": monument["city_id"], "name": f"Bare {uuid.uuid4().hex[:4]}", "type": "monument"},
        headers=admin,
    ).json()
    assert client.post(f"{API}/places/{bare['id']}/ask", json={"question": "Who?"}, headers=traveler).status_code == 409
    assert client.post(url, json={"question": "Who built it?"}, headers=admin).status_code == 403
