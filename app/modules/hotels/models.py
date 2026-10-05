"""Table: hotels. Owner: Person 5."""

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin


class Hotel(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "hotels"

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    stars: Mapped[int | None] = mapped_column(Integer)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    description: Mapped[str | None] = mapped_column(Text)
    amenities: Mapped[list | None] = mapped_column(JSONB)
    image_url: Mapped[str | None] = mapped_column(Text)
