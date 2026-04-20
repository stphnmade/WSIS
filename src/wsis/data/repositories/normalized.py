from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.models import CityProfileRecord
from wsis.data.pipeline.city_profiles import build_city_profiles_dataset
from wsis.data.repositories.base import CityRepository
from wsis.data.validation import CityProfilesValidationError, validate_city_profiles_frame
from wsis.domain.models import CityMetrics


@lru_cache(maxsize=1)
def load_city_profiles() -> tuple[CityProfileRecord, ...]:
    settings = get_settings()
    data_path = Path(settings.processed_city_profiles_path)
    if not data_path.exists():
        return build_city_profiles_dataset()

    try:
        frame = pd.read_parquet(data_path)
        return validate_city_profiles_frame(frame)
    except (CityProfilesValidationError, FileNotFoundError, ValueError):
        return build_city_profiles_dataset(output_path=data_path)


class NormalizedCityRepository(CityRepository):
    def list_city_metrics(self) -> tuple[CityMetrics, ...]:
        return tuple(record.to_city_metrics() for record in load_city_profiles())
