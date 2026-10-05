"""Offer functions other people call. Owner: Person 6.

- best_offers_for_cities(): Person 2's trip generator uses it to pick hotels.
- pause_all_for_company(): Person 1's admin "suspend" uses it.
- create_undercut_alerts(): called here after any price change (alerts for the other companies).
"""

from sqlalchemy.orm import Session


def best_offers_for_cities(db: Session, city_ids: list[int], budget_level: str) -> list[dict]:
    """Return the top active offers per city with hotel name, price and company trust score."""
    raise NotImplementedError("TODO(Person 6)")


def pause_all_for_company(db: Session, company_id: int) -> int:
    """Set every active offer of this company to paused. Returns how many changed."""
    raise NotImplementedError("TODO(Person 6)")


def create_undercut_alerts(db: Session, offer_id: int) -> None:
    """If this offer is now cheaper than other companies' offers for the same hotel and room type,
    create an 'undercut' price_alert for each of those companies."""
    raise NotImplementedError("TODO(Person 6)")
