"""Shared smoke tests: the app starts and every planned endpoint is registered."""

from tests.conftest import API


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_all_endpoints_registered(client):
    spec = client.get("/openapi.json").json()
    ops = [(m, p) for p, v in spec["paths"].items() for m in v if p.startswith(API)]
    # 91 product endpoints + 6 AI endpoints. Update this number when you add or remove an endpoint.
    assert len(ops) == 97


def test_stub_returns_501_with_owner(client):
    res = client.get(f"{API}/hotels/1")
    assert res.status_code == 501
    assert "Person 5" in res.json()["detail"]
