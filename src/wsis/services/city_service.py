from __future__ import annotations

from functools import lru_cache

from wsis.data.repositories.base import CityRepository
from wsis.data.repositories.factory import get_city_repository
from wsis.domain.models import CityDetail, CityMetrics, CitySummary, ScoreWeights
from wsis.scoring.engine import build_city_summary
from wsis.services.reddit import PlaceholderRedditSentimentService, RedditSentimentService


class CityNotFoundError(ValueError):
    """Raised when a city slug does not exist in the current dataset."""


class CityService:
    def __init__(
        self,
        repository: CityRepository | None = None,
        reddit_service: RedditSentimentService | None = None,
    ) -> None:
        self._repository = repository or get_city_repository()
        self._reddit_service = reddit_service or PlaceholderRedditSentimentService()

    def _cities(self) -> list[CityMetrics]:
        return list(self._repository.list_city_metrics())

    def list_cities(self, weights: ScoreWeights | None = None) -> list[CitySummary]:
        active_weights = weights or ScoreWeights()
        cities = self._cities()
        summaries = [build_city_summary(city, cities, active_weights) for city in cities]
        return sorted(summaries, key=lambda summary: summary.overall_score, reverse=True)

    def get_city(self, slug: str, weights: ScoreWeights | None = None) -> CityDetail:
        cities = self._cities()
        city = next((item for item in cities if item.slug == slug), None)
        if city is None:
            raise CityNotFoundError(slug)

        summary = build_city_summary(city, cities, weights or ScoreWeights())
        highlights = [
            f"Median rent is ${city.median_rent:,.0f} per month.",
            f"Median home price is ${city.median_home_price:,.0f}.",
            f"Job growth is {city.job_growth_pct:.1f}% with unemployment at {city.unemployment_pct:.1f}%.",
            "TODO: replace generic highlights with source-backed narratives and neighborhood-level context.",
        ]

        return CityDetail(
            summary=summary,
            metrics=city,
            highlights=highlights,
            reddit_panel=self._reddit_service.get_panel(city),
        )

    def compare_cities(
        self,
        slugs: list[str],
        weights: ScoreWeights | None = None,
    ) -> list[CityDetail]:
        return [self.get_city(slug, weights) for slug in slugs]


@lru_cache(maxsize=1)
def get_city_service() -> CityService:
    return CityService()
