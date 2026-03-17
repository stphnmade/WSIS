from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str
    api_base_url: str
    city_repository_backend: str
    mock_city_data_path: str
    raw_data_dir: str
    processed_city_profiles_path: str
    mapbox_token: str
    request_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    mock_path = Path(os.getenv("WSIS_MOCK_CITY_DATA_PATH", "data/mock/cities.csv"))
    raw_dir = Path(os.getenv("WSIS_RAW_DATA_DIR", "data/raw"))
    processed_path = Path(
        os.getenv("WSIS_PROCESSED_CITY_PROFILES_PATH", "data/processed/city_profiles.parquet")
    )

    mock_city_data_path = mock_path if mock_path.is_absolute() else project_root / mock_path
    raw_data_dir = raw_dir if raw_dir.is_absolute() else project_root / raw_dir
    processed_city_profiles_path = (
        processed_path if processed_path.is_absolute() else project_root / processed_path
    )

    return Settings(
        app_env=os.getenv("WSIS_APP_ENV", "development"),
        api_base_url=os.getenv("WSIS_API_BASE_URL", "http://localhost:8000"),
        city_repository_backend=os.getenv("WSIS_CITY_REPOSITORY_BACKEND", "processed"),
        mock_city_data_path=str(mock_city_data_path),
        raw_data_dir=str(raw_data_dir),
        processed_city_profiles_path=str(processed_city_profiles_path),
        mapbox_token=os.getenv("WSIS_MAPBOX_TOKEN", ""),
        request_timeout_seconds=float(os.getenv("WSIS_REQUEST_TIMEOUT_SECONDS", "3")),
    )
