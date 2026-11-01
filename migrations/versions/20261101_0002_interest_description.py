"""interests: a description line, and icons from the design's icon set

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-01 15:00:00

The traveler app used to keep its own table of icons and descriptions per interest.
Now both live in the database, so an interest the admin adds shows up correctly everywhere.
Old icon keys (pyramid, museum, ...) are renamed to the design's icon names.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_TO_NEW = {
    "pyramid": "history",
    "museum": "image",
    "utensils": "food",
    "waves": "leaf",
    "shopping-bag": "briefcase",
    "landmark": "pin",
    "umbrella": "waves",
}
NEW_TO_OLD = {new: old for old, new in OLD_TO_NEW.items()}

DESCRIPTIONS = {
    "Ancient history": "Temples, tombs and the pyramids",
    "Museums": "Treasures, mummies and old masters",
    "Food": "Street food, cooking and bazaars",
    "Nile and nature": "Felucca rides, gardens and islands",
    "Markets and shopping": "Souks, crafts and spices",
    "Nightlife": "Rooftops and evening Nile cruises",
    "Religious sites": "Mosques, churches and old quarters",
    "Photography": "Viewpoints and golden hours",
}

interests = sa.table(
    "interests", sa.column("name", sa.String), sa.column("icon", sa.String), sa.column("description", sa.String)
)


def upgrade() -> None:
    op.add_column("interests", sa.Column("description", sa.String(length=160), nullable=True))
    # one CASE so "waves" -> "leaf" and "umbrella" -> "waves" don't run into each other
    op.execute(interests.update().values(icon=sa.case(OLD_TO_NEW, value=interests.c.icon, else_=interests.c.icon)))
    for name, text in DESCRIPTIONS.items():
        op.execute(interests.update().where(interests.c.name == name).values(description=text))


def downgrade() -> None:
    op.execute(interests.update().values(icon=sa.case(NEW_TO_OLD, value=interests.c.icon, else_=interests.c.icon)))
    op.drop_column("interests", "description")
