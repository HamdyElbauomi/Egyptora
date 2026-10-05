"""Trust score logic. Owner: Person 1.

trust = (10 × initial_score + n × average_rating) ÷ (10 + n)

The admin's starting score counts as 10 reviews, so it matters a lot for a new company
and fades as real traveler reviews arrive.
Example: (10 × 4.2 + 38 × 4.3) ÷ 48 = 4.28 → 4.3
"""

INITIAL_WEIGHT = 10


def trust_score(initial_score: float, reviews_count: int, average_rating: float | None) -> float:
    if reviews_count == 0 or average_rating is None:
        return round(initial_score, 1)
    total = INITIAL_WEIGHT * initial_score + reviews_count * average_rating
    return round(total / (INITIAL_WEIGHT + reviews_count), 1)


def initial_score_from_checklist(
    license_verified: bool, google_rating: float | None, years_active: int | None, social_presence: int
) -> float:
    """TODO(Person 1): agree on the weights with the team. This is a first guess."""
    if not license_verified:
        return 0.0
    rating_part = google_rating if google_rating is not None else 3.0
    years_part = min(years_active or 0, 10) / 10 * 5
    score = 0.6 * rating_part + 0.2 * years_part + 0.2 * social_presence
    return round(min(score, 5.0), 1)
