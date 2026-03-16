from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.models import CanonicalCityRecord
from wsis.data.pipeline.normalize import build_normalized_city_dataset
from wsis.data.repositories.base import CityRepository
from wsis.domain.models import CityMetrics


@lru_cache(maxsize=1)
def load_canonical_cities() -> tuple[CanonicalCityRecord, ...]:
    settings = get_settings()
    data_path = Path(settings.normalized_city_data_path)
    if not data_path.exists():
        return build_normalized_city_dataset()

    frame = pd.read_csv(data_path, dtype={"county_fips": str})
    return tuple(CanonicalCityRecord.model_validate(record) for record in frame.to_dict("records"))


class NormalizedCityRepository(CityRepository):
    def list_city_metrics(self) -> tuple[CityMetrics, ...]:
        return tuple(record.to_city_metrics() for record in load_canonical_cities())

