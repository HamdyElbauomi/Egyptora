"""Seed: 1 admin, 3 travelers, 4 company users + approved companies. Owner: Person 1.

Dev logins (password for all: egyptora123):
  admin@egyptora.dev, traveler1@egyptora.dev .. traveler3@egyptora.dev,
  sunrise@egyptora.dev, bluelotus@egyptora.dev, nilehorizon@egyptora.dev, pharaohpath@egyptora.dev
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.accounts.models import User
from app.modules.companies.models import Company

PASSWORD = "egyptora123"

COMPANIES = [
    ("sunrise", "Sunrise Travel", 4.4),
    ("bluelotus", "Blue Lotus Tours", 4.2),
    ("nilehorizon", "Nile Horizon", 4.5),
    ("pharaohpath", "Pharaoh Path", 3.9),
]


def _user(db: Session, email: str, name: str, role: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, name=name, role=role, password_hash=hash_password(PASSWORD))
        db.add(user)
        db.flush()
    return user


def seed(db: Session) -> None:
    admin = _user(db, "admin@egyptora.dev", "Egyptora Admin", "admin")
    for i in range(1, 4):
        _user(db, f"traveler{i}@egyptora.dev", f"Traveler {i}", "traveler")
    for slug, name, score in COMPANIES:
        owner = _user(db, f"{slug}@egyptora.dev", name, "company")
        if db.scalar(select(Company).where(Company.owner_user_id == owner.id)) is None:
            db.add(
                Company(
                    owner_user_id=owner.id,
                    name=name,
                    license_no=f"ETA-{slug.upper()}",
                    status="approved",
                    initial_score=score,
                    trust_score=score,
                    approved_by=admin.id,
                    approved_at=datetime.now(UTC),
                )
            )
