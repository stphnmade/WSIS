from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.repositories.base import CityRepository
from wsis.domain.models import CityMetrics, DimensionTrust


def _mock_trust(note: str) -> DimensionTrust:
    return DimensionTrust(
        confidence="estimated",
        source="mock_city_dataset",
        source_date="unknown",
        is_imputed=True,
        note=note,
    )


@lru_cache(maxsize=1)
def load_mock_cities() -> tuple[CityMetrics, ...]:
    settings = get_settings()
    data_path = Path(settings.mock_city_data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Mock city dataset not found at {data_path}")

    frame = pd.read_csv(data_path)
    records = []
    for record in frame.to_dict("records"):
        enriched = {
            **record,
            "violent_crime_per_100k": None,
            "avg_temp_f": None,
            "sunny_days": None,
            "affordability_trust": _mock_trust("Mock-only affordability input."),
            "job_market_trust": _mock_trust("Mock-only job-market input."),
            "safety_trust": _mock_trust("Mock-only safety input."),
            "climate_trust": _mock_trust("Mock-only climate input."),
            "social_trust": DimensionTrust(
                confidence="seeded",
                source="mock_city_dataset",
                source_date="unknown",
                is_imputed=True,
                note="Mock-only social context.",
            ),
            "is_mvp_eligible": False,
        }
        records.append(CityMetrics.model_validate(enriched))
    return tuple(records)


class MockCityRepository(CityRepository):
    def list_city_metrics(self) -> tuple[CityMetrics, ...]:
        return load_mock_cities()
