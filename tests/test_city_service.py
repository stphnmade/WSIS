from wsis.domain.models import ScoreWeights
from wsis.data.repositories.base import CityRepository
from wsis.data.repositories.normalized import load_city_profiles
from wsis.domain.models import DimensionTrust, ScoreWeights
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
    assert detail.reddit_panel.included_in_score is False
    assert detail.reddit_panel.generated_at
    assert detail.reddit_panel.provenance
    assert all("TODO:" not in highlight for highlight in detail.highlights)
    assert "Social sentiment" in detail.summary.score_context.excluded_dimensions
    assert detail.summary.score_context.eligible_for_mvp_ranking is True
    assert detail.metrics.median_home_price_source
    assert detail.metrics.job_growth_source
    assert detail.metrics.median_home_price_source_date
    assert detail.metrics.job_growth_source_date


class _StubRepository(CityRepository):
    def __init__(self, cities):
        self._cities = tuple(cities)

    def list_city_metrics(self):
        return self._cities


def test_list_cities_excludes_ineligible_rows_from_ranked_discovery() -> None:
    cities = [record.to_city_metrics() for record in load_city_profiles()]
    eligible = cities[0]
    ineligible = cities[1].model_copy(
        update={
            "slug": "ineligible-city",
            "is_mvp_eligible": False,
            "job_market_trust": DimensionTrust(
                confidence="estimated",
                source="test_fixture",
                source_date="2026-04-20",
                is_imputed=True,
                note="Estimated in test fixture.",
            ),
        }
    )
    service = CityService(repository=_StubRepository([eligible, ineligible]))

    summaries = service.list_cities(ScoreWeights())

    assert [summary.slug for summary in summaries] == [eligible.slug]


def test_get_city_still_returns_ineligible_city_for_inspection() -> None:
    cities = [record.to_city_metrics() for record in load_city_profiles()]
    ineligible = cities[0].model_copy(
        update={
            "slug": "inspection-only-city",
            "is_mvp_eligible": False,
            "affordability_trust": DimensionTrust(
                confidence="estimated",
                source="test_fixture",
                source_date="2026-04-20",
                is_imputed=True,
                note="Estimated in test fixture.",
            ),
        }
    )
    service = CityService(repository=_StubRepository([ineligible]))

    detail = service.get_city("inspection-only-city", ScoreWeights())

    assert detail.summary.slug == "inspection-only-city"
    assert detail.summary.score_context.eligible_for_mvp_ranking is False
    assert detail.summary.score_context.beta_warning
    assert detail.summary.score_context.exclusion_reasons
