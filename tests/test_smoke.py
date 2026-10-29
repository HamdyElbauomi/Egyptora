"""Shared smoke tests: the app starts and every planned endpoint is registered."""

from app.core.deps import not_implemented
from tests.conftest import API


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_all_endpoints_registered(client):
    spec = client.get("/openapi.json").json()
    ops = [(m, p) for p, v in spec["paths"].items() for m in v if p.startswith(API)]
    # 92 product endpoints + 6 AI endpoints. Update this number when you add or remove an endpoint.
    assert len(ops) == 98


def test_no_endpoint_is_a_stub_anymore():
    """Every planned endpoint is built. not_implemented() stays for new endpoints added as stubs first."""
    from pathlib import Path

    stubs = [str(p) for p in Path("app/modules").rglob("*.py") if "raise not_implemented(" in p.read_text()]
    assert stubs == []
    error = not_implemented("Person 3")
    assert error.status_code == 501 and "Person 3" in error.detail
