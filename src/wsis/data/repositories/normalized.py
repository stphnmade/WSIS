from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.models import CityProfileRecord
from wsis.data.pipeline.city_profiles import build_city_profiles_dataset
from wsis.data.repositories.base import CityRepository
from wsis.domain.models import CityMetrics


@lru_cache(maxsize=1)
def load_city_profiles() -> tuple[CityProfileRecord, ...]:
    settings = get_settings()
    data_path = Path(settings.processed_city_profiles_path)
    if not data_path.exists():
        return build_city_profiles_dataset()

    frame = pd.read_parquet(data_path)
    return tuple(CityProfileRecord.model_validate(record) for record in frame.to_dict("records"))


class NormalizedCityRepository(CityRepository):
    def list_city_metrics(self) -> tuple[CityMetrics, ...]:
        return tuple(record.to_city_metrics() for record in load_city_profiles())
