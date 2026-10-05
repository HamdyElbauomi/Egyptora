"""Tables: places, place_interests, place_images, scans. Owner: Person 4."""

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

PLACE_TYPES = ("monument", "museum", "activity", "food", "nature")
IMAGE_SOURCES = ("admin", "user_scan")


class Place(IdMixin, Base):
    __tablename__ = "places"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(Enum(*PLACE_TYPES, name="place_type"))
    short_description: Mapped[str | None] = mapped_column(Text)
    # The checked history text shown on the camera screen and the only source /ai/ask answers from.
    verified_info: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    era: Mapped[str | None] = mapped_column(String(80))
    opening_hours: Mapped[str | None] = mapped_column(String(120))
    ticket_price: Mapped[int | None] = mapped_column(Integer)
    visit_minutes: Mapped[int | None] = mapped_column(Integer)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    image_url: Mapped[str | None] = mapped_column(Text)
    # Class name the vision model returns, e.g. "karnak_temple". Links a scan to this row.
    recognition_label: Mapped[str | None] = mapped_column(String(80), unique=True)


class PlaceInterest(Base):
    __tablename__ = "place_interests"

    place_id: Mapped[int] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[int] = mapped_column(ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True)


class PlaceImage(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "place_images"

    place_id: Mapped[int] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Enum(*IMAGE_SOURCES, name="image_source"), default="admin")
    used_for_training: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Scan(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "scans"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(Text)
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
