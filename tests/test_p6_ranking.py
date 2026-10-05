"""Person 6 · Lowest and Best value ranking."""

from app.modules.offers.ranking import OfferForRanking, rank


def test_lowest_and_best_value():
    offers = [
        OfferForRanking(1, 1200, 3.5, False),  # cheapest, low trust
        OfferForRanking(2, 1280, 4.6, True),  # a bit more, trusted, free cancellation
        OfferForRanking(3, 1450, 3.9, False),
    ]
    result = rank(offers)
    assert result["lowest"] == 1
    assert result["best_value"] == 2
