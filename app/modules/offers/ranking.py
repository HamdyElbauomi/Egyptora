"""Lowest and Best value ranking for competing offers. Owner: Person 6.

TODO(team decision): agree on the Best value weights before building GET /hotels/{id}/offers.
The numbers below are a placeholder, not a decision.
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


def best_value_score(offer: OfferForRanking, cheapest: int, most_expensive: int) -> float:
    """Higher is better. Price is scaled so the cheapest offer for the hotel gets 1.0."""
    spread = max(most_expensive - cheapest, 1)
    price_part = 1 - (offer.price_per_night - cheapest) / spread
    trust_part = (offer.trust_score or 0) / 5
    cancel_part = 1.0 if offer.free_cancellation else 0.0
    return PRICE_WEIGHT * price_part + TRUST_WEIGHT * trust_part + CANCELLATION_WEIGHT * cancel_part


def rank(offers: list[OfferForRanking]) -> dict:
    """Returns {"lowest": offer_id, "best_value": offer_id, "order": [offer_id, ...]} sorted by best value."""
    if not offers:
        return {"lowest": None, "best_value": None, "order": []}
    prices = [o.price_per_night for o in offers]
    lo, hi = min(prices), max(prices)
    ordered = sorted(offers, key=lambda o: best_value_score(o, lo, hi), reverse=True)
    lowest = min(offers, key=lambda o: o.price_per_night)
    return {"lowest": lowest.offer_id, "best_value": ordered[0].offer_id, "order": [o.offer_id for o in ordered]}
