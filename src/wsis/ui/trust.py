from __future__ import annotations

from wsis.core.config import get_settings
from wsis.core.freshness import source_freshness_label
from wsis.domain.models import CityDetail, ScoreDimension


def freshness_badge(source_date: str) -> str:
    settings = get_settings()
    freshness = source_freshness_label(source_date, settings.source_stale_after_days)
    labels = {
        "current": "Current",
        "aging": "Aging",
        "stale": "Stale",
        "unknown": "Unknown",
    }
    return labels[freshness]


def dimension_freshness_summary(dimension: ScoreDimension) -> str:
    return f"{dimension.label}: {freshness_badge(dimension.source_date)} ({dimension.source_date})"


def city_core_freshness_summary(detail: CityDetail) -> list[str]:
    return [
        dimension_freshness_summary(dimension)
        for dimension in detail.summary.score_dimensions
        if dimension.key in {"affordability", "job_market", "safety", "climate"}
    ]
