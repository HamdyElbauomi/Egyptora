"""Lowest and Best value ranking for competing offers. Owner: Person 6.

Used by GET /hotels/{id}/offers (badges and order) and by the trip planner (which hotel to pick).
TODO(team decision): the weights below are a starting point; tune them once real offers exist.
"""

from dataclasses import dataclass

PRICE_WEIGHT = 0.5
TRUST_WEIGHT = 0.35
CANCELLATION_WEIGHT = 0.15


@dataclass
class OfferForRanking:
    offer_id: int
    price_per_night: int
    trust_score: float | None  # 0..5, from Person 1's companies table
    free_cancellation: bool


def best_value_score(offer: OfferForRanking, cheapest: int) -> float:
    """Higher is better (0..1). Price is relative to the cheapest offer: the cheapest gets 1.0,
    an offer 10% pricier gets about 0.91. So a small price gap can be beaten by a more trusted
    company or free cancellation, but a big gap can't."""
    price_part = cheapest / max(offer.price_per_night, 1)
    trust_part = (offer.trust_score or 0) / 5
    cancel_part = 1.0 if offer.free_cancellation else 0.0
    return PRICE_WEIGHT * price_part + TRUST_WEIGHT * trust_part + CANCELLATION_WEIGHT * cancel_part


def rank(offers: list[OfferForRanking]) -> dict:
    """Returns {"lowest": offer_id, "best_value": offer_id, "order": [offer_id, ...]} sorted by best value."""
    if not offers:
        return {"lowest": None, "best_value": None, "order": []}
    lo = min(o.price_per_night for o in offers)
    ordered = sorted(offers, key=lambda o: (-best_value_score(o, lo), o.price_per_night, o.offer_id))
    lowest = min(offers, key=lambda o: o.price_per_night)
    return {"lowest": lowest.offer_id, "best_value": ordered[0].offer_id, "order": [o.offer_id for o in ordered]}
