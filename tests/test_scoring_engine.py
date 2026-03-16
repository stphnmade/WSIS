from wsis.data.repositories.normalized import load_canonical_cities
from wsis.domain.models import ScoreWeights
from wsis.scoring.engine import build_score_breakdown


def test_score_weights_are_normalized() -> None:
    weights = ScoreWeights(
        affordability=40,
        job_market=25,
        safety=15,
        climate=10,
        social_sentiment=10,
    ).normalized()

    total = (
        weights.affordability
        + weights.job_market
        + weights.safety
        + weights.climate
        + weights.social_sentiment
    )

    assert round(total, 6) == 1.0


def test_breakdown_scores_stay_within_expected_bounds() -> None:
    cities = [record.to_city_metrics() for record in load_canonical_cities()]
    breakdown = build_score_breakdown(cities[0], cities, ScoreWeights())

    assert 0 <= breakdown.affordability <= 10
    assert 0 <= breakdown.job_market <= 10
    assert 0 <= breakdown.safety <= 10
    assert 0 <= breakdown.climate <= 10
    assert 0 <= breakdown.social_sentiment <= 10
    assert 0 <= breakdown.total <= 10
