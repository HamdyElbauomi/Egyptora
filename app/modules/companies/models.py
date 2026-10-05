"""Tables: companies, reviews. Owner: Person 1."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

COMPANY_STATUSES = ("pending", "approved", "rejected", "suspended")
SENTIMENTS = ("positive", "neutral", "negative")


class Company(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "companies"

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    license_no: Mapped[str | None] = mapped_column(String(80))
    license_doc_url: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(40))
    website: Mapped[str | None] = mapped_column(Text)
    facebook_url: Mapped[str | None] = mapped_column(Text)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    google_rating: Mapped[float | None] = mapped_column(Numeric(2, 1))
    years_active: Mapped[int | None] = mapped_column(Integer)
    # Set by the admin checklist on approval; counts as 10 reviews in the trust formula (see trust.py).
    initial_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    trust_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        Enum(*COMPANY_STATUSES, name="company_status"), default="pending", server_default="pending"
    )
    reject_reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Review(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "trip_id", "company_id", name="uq_review_once_per_trip"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),
    )

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trip_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("trips.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(Enum(*SENTIMENTS, name="review_sentiment"))
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
