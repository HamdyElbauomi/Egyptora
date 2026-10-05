"""Person 1 · trust score formula."""

from app.modules.companies.trust import trust_score


def test_example_from_design():
    assert trust_score(4.2, 38, 4.3) == 4.3


def test_no_reviews_uses_initial_score():
    assert trust_score(4.0, 0, None) == 4.0
