"""Table: users. Owner: Person 1."""

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

USER_ROLES = ("traveler", "company", "admin")


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Enum(*USER_ROLES, name="user_role"), default="traveler")
    language: Mapped[str] = mapped_column(String(8), default="en", server_default="en")
