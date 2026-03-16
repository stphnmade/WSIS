from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str
    api_base_url: str
    city_data_path: str
    mapbox_token: str
    request_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    configured_path = Path(os.getenv("WSIS_CITY_DATA_PATH", "data/mock/cities.csv"))
    city_data_path = configured_path if configured_path.is_absolute() else project_root / configured_path

    return Settings(
        app_env=os.getenv("WSIS_APP_ENV", "development"),
        api_base_url=os.getenv("WSIS_API_BASE_URL", "http://localhost:8000"),
        city_data_path=str(city_data_path),
        mapbox_token=os.getenv("WSIS_MAPBOX_TOKEN", ""),
        request_timeout_seconds=float(os.getenv("WSIS_REQUEST_TIMEOUT_SECONDS", "3")),
    )

