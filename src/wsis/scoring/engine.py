from __future__ import annotations

from dataclasses import dataclass

from wsis.domain.models import (
    CityMetrics,
    CitySummary,
    DimensionTrust,
    ScoreBreakdown,
    ScoreContext,
    ScoreDimension,
    ScoreWeights,
)


@dataclass(frozen=True)
class _DatasetStats:
    min_rent_burden: float
    max_rent_burden: float
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
    unemployment = [city.unemployment_pct for city in cities]

    return _DatasetStats(
        min_rent_burden=min(rent_burdens),
        max_rent_burden=max(rent_burdens),
        min_unemployment=min(unemployment),
        max_unemployment=max(unemployment),
    )


def _overall_confidence(city: CityMetrics) -> str:
    ranked_confidences = [
        city.affordability_trust.confidence,
        city.job_market_trust.confidence,
        city.safety_trust.confidence,
        city.climate_trust.confidence,
    ]
    if city.is_mvp_eligible:
        return "source_backed"
    if "missing" in ranked_confidences:
        return "missing"
    return "estimated"


def _score_dimension(
    key: str,
    label: str,
    score: float,
    trust: DimensionTrust,
    included_in_score: bool,
) -> ScoreDimension:
    return ScoreDimension(
        key=key,
        label=label,
        score=score,
        confidence=trust.confidence,
        included_in_score=included_in_score,
        source=trust.source,
        source_date=trust.source_date,
        is_imputed=trust.is_imputed,
        note=trust.note,
    )


def _score_context(city: CityMetrics, dimensions: list[ScoreDimension]) -> ScoreContext:
    included = [dimension.label for dimension in dimensions if dimension.included_in_score]
    excluded = [dimension.label for dimension in dimensions if not dimension.included_in_score]
    explanation = (
        "WSIS ranks cities using affordability, job market, safety, and climate when those inputs "
        "are source-backed. Social sentiment stays visible as context and does not change the score."
    )
    beta_warning = None
    if not city.is_mvp_eligible:
        beta_warning = (
            "This city has at least one estimated core dimension, so it is shown for inspection only "
            "and excluded from ranked discovery."
        )
    return ScoreContext(
        overall_confidence=_overall_confidence(city),
        eligible_for_mvp_ranking=city.is_mvp_eligible,
        included_dimensions=included,
        excluded_dimensions=excluded,
        explanation=explanation,
        beta_warning=beta_warning,
    )


def build_score_breakdown(
    city: CityMetrics,
    peers: list[CityMetrics],
    weights: ScoreWeights,
) -> ScoreBreakdown:
    normalized_weights = weights.ranking_normalized()
    stats = _dataset_stats(peers)

    rent_burden = (city.median_rent * 12) / city.median_income

    affordability = round(
        _scale(rent_burden, stats.min_rent_burden, stats.max_rent_burden, invert=True),
        2,
    )
    job_market = round(
        _scale(city.unemployment_pct, stats.min_unemployment, stats.max_unemployment, invert=True),
        2,
    )
    safety = round(city.safety_score_raw / 10, 2)
    climate = round(city.climate_score_raw / 10, 2)
    social_sentiment = round((city.social_sentiment_raw + 1) * 5, 2)

    total = round(
        (
            (affordability * normalized_weights.affordability)
            + (job_market * normalized_weights.job_market)
            + (safety * normalized_weights.safety)
            + (climate * normalized_weights.climate)
        ),
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
    dimensions = [
        _score_dimension(
            "affordability",
            "Affordability",
            breakdown.affordability,
            city.affordability_trust,
            city.affordability_trust.confidence == "source_backed",
        ),
        _score_dimension(
            "job_market",
            "Job market",
            breakdown.job_market,
            city.job_market_trust,
            city.job_market_trust.confidence == "source_backed",
        ),
        _score_dimension(
            "safety",
            "Safety",
            breakdown.safety,
            city.safety_trust,
            city.safety_trust.confidence == "source_backed",
        ),
        _score_dimension(
            "climate",
            "Climate",
            breakdown.climate,
            city.climate_trust,
            city.climate_trust.confidence == "source_backed",
        ),
        _score_dimension(
            "social_sentiment",
            "Social sentiment",
            breakdown.social_sentiment,
            city.social_trust,
            False,
        ),
    ]
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
        score_dimensions=dimensions,
        score_context=_score_context(city, dimensions),
    )
