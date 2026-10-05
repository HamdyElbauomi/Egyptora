"""Tables: offers, price_alerts + the hotel_best_price view. Owner: Person 6."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

OFFER_STATUSES = ("active", "paused", "expired", "flagged")
ALERT_TYPES = ("undercut", "price_anomaly")


class Offer(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("hotel_id", "company_id", "room_type", name="uq_offer_per_room_type"),)

    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    room_type: Mapped[str] = mapped_column(String(60))
    price_per_night: Mapped[int] = mapped_column(Integer)  # whole EGP
    breakfast_included: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    free_cancellation: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    cancellation_days: Mapped[int | None] = mapped_column(Integer)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        Enum(*OFFER_STATUSES, name="offer_status"), default="active", server_default="active"
    )
    flag_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PriceAlert(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "price_alerts"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(Enum(*ALERT_TYPES, name="alert_type"))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


# Read-only view, created by SQL in the migration (not by SQLAlchemy). NL-to-SQL (Person 5) reads it.
# info={"is_view": True} tells Alembic autogenerate to ignore it.
hotel_best_price = Table(
    "hotel_best_price",
    Base.metadata,
    Column("hotel_id", BigInteger, primary_key=True),
    Column("city_id", BigInteger),
    Column("hotel_name", String),
    Column("stars", Integer),
    Column("min_price", Integer),
    Column("offers_count", Integer),
    Column("best_company_id", BigInteger),
    info={"is_view": True},
)

HOTEL_BEST_PRICE_SQL = """
CREATE OR REPLACE VIEW hotel_best_price AS
SELECT h.id AS hotel_id,
       h.city_id,
       h.name AS hotel_name,
       h.stars,
       best.price_per_night AS min_price,
       counts.offers_count,
       best.company_id AS best_company_id
FROM hotels h
JOIN (
    SELECT hotel_id, COUNT(*)::int AS offers_count
    FROM offers WHERE status = 'active' GROUP BY hotel_id
) counts ON counts.hotel_id = h.id
JOIN LATERAL (
    SELECT o.price_per_night, o.company_id
    FROM offers o
    WHERE o.hotel_id = h.id AND o.status = 'active'
    ORDER BY o.price_per_night ASC
    LIMIT 1
) best ON TRUE;
"""
