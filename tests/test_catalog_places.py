"""Feature: catalog (cities, interests) and places."""

import pytest

from tests.conftest import API, auth_header

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.fixture
def admin(client):
    return auth_header(client, "catalog-admin@test.dev", role="admin")


@pytest.fixture
def traveler(client):
    return auth_header(client, "catalog-traveler@test.dev")


def make_city(client, admin, name):
    res = client.post(f"{API}/admin/cities", json={"name": name}, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


def make_interest(client, admin, name):
    res = client.post(f"{API}/admin/interests", json={"name": name}, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


def make_place(client, admin, **fields):
    body = {"type": "monument", **fields}
    res = client.post(f"{API}/admin/places", json=body, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


# ---------- cities and interests ----------


def test_city_crud_and_unique_name(client, admin):
    city = make_city(client, admin, "Alexandria")
    assert city["name"] == "Alexandria"
    assert client.post(f"{API}/admin/cities", json={"name": "alexandria"}, headers=admin).status_code == 409

    res = client.patch(f"{API}/admin/cities/{city['id']}", json={"description": "On the Mediterranean"}, headers=admin)
    assert res.status_code == 200
    assert res.json()["description"] == "On the Mediterranean"
    assert res.json()["name"] == "Alexandria"  # untouched field stays
    assert client.patch(f"{API}/admin/cities/999999", json={"name": "X City"}, headers=admin).status_code == 404


def test_interest_crud_and_unique_name(client, admin):
    interest = make_interest(client, admin, "Diving")
    assert client.post(f"{API}/admin/interests", json={"name": "DIVING"}, headers=admin).status_code == 409
    res = client.patch(f"{API}/admin/interests/{interest['id']}", json={"icon": "waves"}, headers=admin)
    assert res.json()["icon"] == "waves"


def test_admin_routes_need_admin(client, traveler):
    assert client.post(f"{API}/admin/cities", json={"name": "Siwa"}).status_code == 401
    assert client.post(f"{API}/admin/cities", json={"name": "Siwa"}, headers=traveler).status_code == 403


def test_public_lookups(client, admin):
    city = make_city(client, admin, "Dahab")
    snorkeling = make_interest(client, admin, "Snorkeling")
    make_place(client, admin, city_id=city["id"], name="Blue Hole", type="nature")
    cities = {c["name"]: c for c in client.get(f"{API}/cities").json()}  # public, no token
    assert cities["Dahab"]["places_count"] == 1
    interests = {i["name"]: i for i in client.get(f"{API}/interests").json()}
    assert interests["Snorkeling"]["id"] == snorkeling["id"]


# ---------- places ----------


def test_place_create_read_update_delete(client, admin):
    city = make_city(client, admin, "Edfu")
    history = make_interest(client, admin, "Temples")
    place = make_place(
        client,
        admin,
        city_id=city["id"],
        name="Temple of Horus",
        verified_info="Ptolemaic temple dedicated to Horus.",
        recognition_label="edfu_temple",
        interest_ids=[history["id"]],
    )
    assert place["interest_ids"] == [history["id"]]

    detail = client.get(f"{API}/places/{place['id']}").json()  # public, no token
    assert detail["city_name"] == "Edfu"
    assert detail["images"] == []

    res = client.patch(
        f"{API}/admin/places/{place['id']}", json={"visit_minutes": 75, "interest_ids": []}, headers=admin
    )
    assert res.json()["visit_minutes"] == 75
    assert res.json()["interest_ids"] == []
    assert res.json()["verified_info"] == "Ptolemaic temple dedicated to Horus."

    assert client.delete(f"{API}/admin/places/{place['id']}", headers=admin).status_code == 204
    assert client.get(f"{API}/places/{place['id']}").status_code == 404


def test_place_validation(client, admin):
    city = make_city(client, admin, "Kom Ombo")
    bad_city = client.post(
        f"{API}/admin/places", json={"city_id": 999999, "name": "X place", "type": "monument"}, headers=admin
    )
    assert bad_city.status_code == 400
    bad_interest = client.post(
        f"{API}/admin/places",
        json={"city_id": city["id"], "name": "Y place", "type": "monument", "interest_ids": [999999]},
        headers=admin,
    )
    assert bad_interest.status_code == 400
    bad_type = client.post(
        f"{API}/admin/places", json={"city_id": city["id"], "name": "Z place", "type": "castle"}, headers=admin
    )
    assert bad_type.status_code == 422

    make_place(client, admin, city_id=city["id"], name="Kom Ombo Temple", recognition_label="kom_ombo")
    dup = client.post(
        f"{API}/admin/places",
        json={"city_id": city["id"], "name": "Copy", "type": "monument", "recognition_label": "kom_ombo"},
        headers=admin,
    )
    assert dup.status_code == 409


def test_place_list_filters_and_pagination(client, admin):
    city = make_city(client, admin, "Fayoum")
    for i in range(3):
        make_place(client, admin, city_id=city["id"], name=f"Fayoum spot {i}", type="nature")
    make_place(client, admin, city_id=city["id"], name="Fayoum museum", type="museum")

    page = client.get(f"{API}/admin/places", params={"city_id": city["id"], "limit": 2}, headers=admin).json()
    assert page["total"] == 4 and len(page["data"]) == 2 and page["page"] == 1
    nature = client.get(f"{API}/admin/places", params={"city_id": city["id"], "type": "nature"}, headers=admin).json()
    assert nature["total"] == 3
    found = client.get(f"{API}/admin/places", params={"search": "MUSEUM", "city_id": city["id"]}, headers=admin).json()
    assert [p["name"] for p in found["data"]] == ["Fayoum museum"]


def test_place_images_upload_and_delete(client, admin):
    city = make_city(client, admin, "Minya")
    place = make_place(client, admin, city_id=city["id"], name="Beni Hasan")
    files = [("files", ("a.png", PNG, "image/png")), ("files", ("b.png", PNG, "image/png"))]
    res = client.post(f"{API}/admin/places/{place['id']}/images", files=files, headers=admin)
    assert res.status_code == 201, res.text
    images = res.json()
    assert len(images) == 2
    assert client.get(images[0]["image_url"]).status_code == 200  # file is served

    wrong = client.post(
        f"{API}/admin/places/{place['id']}/images", files=[("files", ("a.txt", b"hi", "text/plain"))], headers=admin
    )
    assert wrong.status_code == 400

    assert client.delete(f"{API}/admin/place-images/{images[0]['id']}", headers=admin).status_code == 204
    assert client.get(images[0]["image_url"]).status_code == 404  # file removed
    assert len(client.get(f"{API}/places/{place['id']}").json()["images"]) == 1


# ---------- suggest ----------


def test_suggest_ranks_cities_by_matching_places(client, admin):
    beach = make_interest(client, admin, "Beaches")
    quiet = make_city(client, admin, "Marsa Alam")
    busy = make_city(client, admin, "Hurghada")
    make_place(client, admin, city_id=busy["id"], name="Giftun Island", type="nature", interest_ids=[beach["id"]])
    make_place(client, admin, city_id=busy["id"], name="Mahmya", type="nature", interest_ids=[beach["id"]])
    make_place(client, admin, city_id=quiet["id"], name="Abu Dabbab", type="nature", interest_ids=[beach["id"]])

    res = client.get(f"{API}/cities/suggest", params={"interests": [beach["id"]], "days": 5}).json()
    assert res["recommended_count"] == 2
    top = res["suggestions"][:2]
    assert [s["city"]["name"] for s in top] == ["Hurghada", "Marsa Alam"]
    assert [s["matching_places"] for s in top] == [2, 1]
    assert all(s["selected"] for s in top)
    assert not any(s["selected"] for s in res["suggestions"][2:])

    assert client.get(f"{API}/cities/suggest", params={"interests": [999999]}).status_code == 400
