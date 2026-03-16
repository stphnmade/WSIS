from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.domain.models import CityMetrics


@lru_cache(maxsize=1)
def load_mock_cities() -> tuple[CityMetrics, ...]:
    settings = get_settings()
    data_path = Path(settings.city_data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Mock city dataset not found at {data_path}")

    frame = pd.read_csv(data_path)
    return tuple(CityMetrics.model_validate(record) for record in frame.to_dict("records"))

