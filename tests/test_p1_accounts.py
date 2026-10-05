"""Person 1 · auth and roles."""

from tests.conftest import API, auth_header


def test_register_login_me(client):
    res = client.post(
        f"{API}/auth/register", json={"name": "Mona", "email": "mona@test.dev", "password": "password123"}
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    me = client.get(f"{API}/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "mona@test.dev"
    assert me.json()["role"] == "traveler"
    assert (
        client.post(f"{API}/auth/login", json={"email": "mona@test.dev", "password": "wrong-pass"}).status_code == 401
    )


def test_duplicate_email_rejected(client):
    body = {"name": "Ali", "email": "ali@test.dev", "password": "password123"}
    client.post(f"{API}/auth/register", json=body)
    assert client.post(f"{API}/auth/register", json=body).status_code == 409


def test_refresh_token(client):
    res = client.post(
        f"{API}/auth/register", json={"name": "Omar", "email": "omar@test.dev", "password": "password123"}
    )
    refreshed = client.post(f"{API}/auth/refresh", json={"refresh_token": res.json()["refresh_token"]})
    assert refreshed.status_code == 200
    bad = client.post(f"{API}/auth/refresh", json={"refresh_token": res.json()["access_token"]})
    assert bad.status_code == 401


def test_role_check(client):
    traveler = auth_header(client, "t1@test.dev")
    admin = auth_header(client, "a1@test.dev", role="admin")
    assert client.get(f"{API}/admin/stats", headers=traveler).status_code == 403
    assert client.get(f"{API}/admin/stats", headers=admin).status_code == 501  # allowed, not built yet
    assert client.get(f"{API}/admin/stats").status_code == 401
