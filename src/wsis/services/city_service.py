from __future__ import annotations

from functools import lru_cache

from wsis.data.repositories.base import CityRepository
from wsis.data.repositories.factory import get_city_repository
from wsis.domain.models import CityDetail, CityMetrics, CitySummary, ScoreWeights
from wsis.scoring.engine import build_city_summary
from wsis.services.reddit import PrecomputedRedditSentimentService, RedditSentimentService


class CityNotFoundError(ValueError):
    """Raised when a city slug does not exist in the current dataset."""


class CityService:
    def __init__(
        self,
        repository: CityRepository | None = None,
        reddit_service: RedditSentimentService | None = None,
    ) -> None:
        self._repository = repository or get_city_repository()
        self._reddit_service = reddit_service or PrecomputedRedditSentimentService()

    def _cities(self) -> list[CityMetrics]:
        return list(self._repository.list_city_metrics())

    def _eligible_cities(self, cities: list[CityMetrics]) -> list[CityMetrics]:
        eligible = [city for city in cities if city.is_mvp_eligible]
        return eligible or cities

    def list_cities(self, weights: ScoreWeights | None = None) -> list[CitySummary]:
        active_weights = weights or ScoreWeights()
        cities = self._cities()
        ranked_cities = self._eligible_cities(cities)
        summaries = [build_city_summary(city, ranked_cities, active_weights) for city in ranked_cities]
        return sorted(summaries, key=lambda summary: summary.overall_score, reverse=True)

    def get_city(self, slug: str, weights: ScoreWeights | None = None) -> CityDetail:
        cities = self._cities()
        ranked_cities = self._eligible_cities(cities)
        city = next((item for item in cities if item.slug == slug), None)
        if city is None:
            raise CityNotFoundError(slug)

        summary = build_city_summary(city, ranked_cities, weights or ScoreWeights())
        reddit_panel = self._reddit_service.get_panel(city)

        return CityDetail(
            summary=summary,
            metrics=city,
            highlights=_build_highlights(city, summary),
            reddit_panel=reddit_panel,
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


def _build_highlights(city: CityMetrics, summary: CitySummary) -> list[str]:
    rent_burden_pct = (city.median_rent * 12 / city.median_income) * 100
    home_price_note = (
        "source-backed local context"
        if not city.median_home_price_is_imputed
        else "estimated fallback context"
    )
    job_growth_note = (
        "source-backed local context"
        if not city.job_growth_is_imputed
        else "estimated fallback context"
    )
    highlights = [
        f"Median rent is about {rent_burden_pct:.0f}% of local median income, at roughly ${city.median_rent:,.0f} per month.",
        f"HUD fair-market rent context is about ${city.fair_market_rent:,.0f}, putting local median rent at {city.rent_to_fmr_ratio:.2f}x FMR.",
        f"Median home price is about ${city.median_home_price:,.0f} ({home_price_note}), with unemployment at {city.unemployment_pct:.1f}%.",
        f"Job growth context is about {city.job_growth_pct:.1f}% ({job_growth_note}), visible for inspection but not required for the ranked MVP score.",
    ]

    if summary.score_context.beta_warning:
        highlights.append(summary.score_context.beta_warning)
    else:
        highlights.append("This city meets the current MVP trust threshold for ranked discovery.")

    if summary.score_breakdown.affordability >= 7:
        highlights.append("Affordability is one of this city's clearer strengths versus the current peer set.")
    elif summary.score_breakdown.affordability <= 4:
        highlights.append("Housing costs look tighter than the strongest affordability peers in this dataset.")

    if summary.score_breakdown.job_market >= 7:
        highlights.append("Job-market momentum is a relative plus for this city in the current scoring cohort.")

    if city.violent_crime_per_100k is not None:
        highlights.append(
            f"Reported violent crime is about {city.violent_crime_per_100k:,.0f} incidents per 100k residents in the current source slice."
        )
    elif summary.score_breakdown.safety >= 7:
        highlights.append("Safety lands on the stronger side of the current peer cohort.")

    if city.avg_temp_f is not None and city.sunny_days is not None:
        highlights.append(
            f"Climate expectations are anchored by an average temperature near {city.avg_temp_f:.0f}F and about {city.sunny_days:.0f} sunny days per year."
        )
    elif summary.score_breakdown.climate >= 7:
        highlights.append("Climate comfort is one of the more favorable parts of this city's profile.")

    return highlights[:5]
