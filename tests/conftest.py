"""Test setup: a separate database (egyptora_test) rebuilt for each test session.

Run: pytest
"""

import os
import tempfile

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://egyptora:egyptora@localhost:5432/egyptora_test")
os.environ["AI_MOCK"] = "true"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="egyptora-uploads-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.offers.models import HOTEL_BEST_PRICE_SQL  # noqa: E402

API = "/api/v1"
REAL_TABLES = [t for t in Base.metadata.sorted_tables if not t.info.get("is_view")]


@pytest.fixture(scope="session", autouse=True)
def database():
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS hotel_best_price"))
    Base.metadata.drop_all(engine, tables=REAL_TABLES)
    Base.metadata.create_all(engine, tables=REAL_TABLES)
    with engine.begin() as conn:
        conn.execute(text(HOTEL_BEST_PRICE_SQL))
    yield
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS hotel_best_price"))
    Base.metadata.drop_all(engine, tables=REAL_TABLES)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(client: TestClient, email: str, role: str = "traveler") -> dict:
    """Register (or log in) a user and return an Authorization header. Changes role directly in the DB."""
    from app.modules.accounts.models import User

    res = client.post(f"{API}/auth/register", json={"name": "Test", "email": email, "password": "password123"})
    if res.status_code == 409:
        res = client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})
    if role != "traveler":
        with SessionLocal() as s:
            user = s.query(User).filter_by(email=email).one()
            user.role = role
            s.commit()
        res = client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
