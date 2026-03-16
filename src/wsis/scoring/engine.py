from __future__ import annotations

from dataclasses import dataclass

from wsis.domain.models import CityMetrics, CitySummary, ScoreBreakdown, ScoreWeights


@dataclass(frozen=True)
class _DatasetStats:
    min_rent_burden: float
    max_rent_burden: float
    min_home_price_ratio: float
    max_home_price_ratio: float
    min_job_growth: float
    max_job_growth: float
    min_unemployment: float
    max_unemployment: float


def _scale(value: float, minimum: float, maximum: float, invert: bool = False) -> float:
    if maximum == minimum:
        return 5.0

    ratio = (value - minimum) / (maximum - minimum)
    ratio = max(0.0, min(1.0, ratio))
    if invert:
        ratio = 1 - ratio

    return round(ratio * 10, 2)


def _dataset_stats(cities: list[CityMetrics]) -> _DatasetStats:
    rent_burdens = [(city.median_rent * 12) / city.median_income for city in cities]
    home_price_ratios = [city.median_home_price / city.median_income for city in cities]
    job_growth = [city.job_growth_pct for city in cities]
    unemployment = [city.unemployment_pct for city in cities]

    return _DatasetStats(
        min_rent_burden=min(rent_burdens),
        max_rent_burden=max(rent_burdens),
        min_home_price_ratio=min(home_price_ratios),
        max_home_price_ratio=max(home_price_ratios),
        min_job_growth=min(job_growth),
        max_job_growth=max(job_growth),
        min_unemployment=min(unemployment),
        max_unemployment=max(unemployment),
    )


def build_score_breakdown(
    city: CityMetrics,
    peers: list[CityMetrics],
    weights: ScoreWeights,
) -> ScoreBreakdown:
    normalized_weights = weights.normalized()
    stats = _dataset_stats(peers)

    rent_burden = (city.median_rent * 12) / city.median_income
    home_price_ratio = city.median_home_price / city.median_income

    affordability = round(
        (_scale(rent_burden, stats.min_rent_burden, stats.max_rent_burden, invert=True) * 0.7)
        + (
            _scale(
                home_price_ratio,
                stats.min_home_price_ratio,
                stats.max_home_price_ratio,
                invert=True,
            )
            * 0.3
        ),
        2,
    )
    job_market = round(
        (_scale(city.job_growth_pct, stats.min_job_growth, stats.max_job_growth) * 0.6)
        + (
            _scale(
                city.unemployment_pct,
                stats.min_unemployment,
                stats.max_unemployment,
                invert=True,
            )
            * 0.4
        ),
        2,
    )
    safety = round(city.safety_score_raw / 10, 2)
    climate = round(city.climate_score_raw / 10, 2)
    social_sentiment = round((city.social_sentiment_raw + 1) * 5, 2)

    total = round(
        (affordability * normalized_weights.affordability)
        + (job_market * normalized_weights.job_market)
        + (safety * normalized_weights.safety)
        + (climate * normalized_weights.climate)
        + (social_sentiment * normalized_weights.social_sentiment),
        2,
    )

    return ScoreBreakdown(
        affordability=affordability,
        job_market=job_market,
        safety=safety,
        climate=climate,
        social_sentiment=social_sentiment,
        total=total,
    )


def build_city_summary(
    city: CityMetrics,
    peers: list[CityMetrics],
    weights: ScoreWeights,
) -> CitySummary:
    breakdown = build_score_breakdown(city, peers, weights)
    return CitySummary(
        slug=city.slug,
        name=city.name,
        state=city.state,
        state_code=city.state_code,
        region=city.region,
        headline=city.headline,
        population=city.population,
        latitude=city.latitude,
        longitude=city.longitude,
        overall_score=breakdown.total,
        score_breakdown=breakdown,
    )

