"""Tables: cities, interests. Owner: Person 3."""

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IdMixin


class City(IdMixin, Base):
    __tablename__ = "cities"

    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    image_url: Mapped[str | None] = mapped_column(Text)


class Interest(IdMixin, Base):
    __tablename__ = "interests"

    name: Mapped[str] = mapped_column(String(60), unique=True)
    icon: Mapped[str | None] = mapped_column(String(60))
