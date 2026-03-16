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
    source_data_dir: str
    normalized_city_data_path: str
    mapbox_token: str
    request_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    mock_path = Path(os.getenv("WSIS_MOCK_CITY_DATA_PATH", "data/mock/cities.csv"))
    source_dir = Path(os.getenv("WSIS_SOURCE_DATA_DIR", "data/source_samples"))
    normalized_path = Path(
        os.getenv("WSIS_NORMALIZED_CITY_DATA_PATH", "data/normalized/city_dataset.csv")
    )

    mock_city_data_path = mock_path if mock_path.is_absolute() else project_root / mock_path
    source_data_dir = source_dir if source_dir.is_absolute() else project_root / source_dir
    normalized_city_data_path = (
        normalized_path if normalized_path.is_absolute() else project_root / normalized_path
    )

    return Settings(
        app_env=os.getenv("WSIS_APP_ENV", "development"),
        api_base_url=os.getenv("WSIS_API_BASE_URL", "http://localhost:8000"),
        city_repository_backend=os.getenv("WSIS_CITY_REPOSITORY_BACKEND", "normalized"),
        mock_city_data_path=str(mock_city_data_path),
        source_data_dir=str(source_data_dir),
        normalized_city_data_path=str(normalized_city_data_path),
        mapbox_token=os.getenv("WSIS_MAPBOX_TOKEN", ""),
        request_timeout_seconds=float(os.getenv("WSIS_REQUEST_TIMEOUT_SECONDS", "3")),
    )
