from wsis.domain.models import ScoreWeights
from wsis.services.city_service import CityService


def test_list_cities_returns_sorted_scores() -> None:
    service = CityService()

    cities = service.list_cities(ScoreWeights())

    assert len(cities) >= 5
    assert cities == sorted(cities, key=lambda city: city.overall_score, reverse=True)


def test_get_city_returns_detail_with_reddit_panel() -> None:
    service = CityService()

    detail = service.get_city("austin-tx", ScoreWeights())

    assert detail.summary.slug == "austin-tx"
    assert detail.reddit_panel.posts
    assert detail.reddit_panel.source == "precomputed_city_sentiment"
    assert detail.reddit_panel.generated_at
    assert detail.reddit_panel.provenance
    assert all("TODO:" not in highlight for highlight in detail.highlights)
