from __future__ import annotations

from functools import lru_cache

from wsis.core.config import get_settings
from wsis.data.repositories.base import CityRepository
from wsis.data.repositories.mock import MockCityRepository
from wsis.data.repositories.normalized import NormalizedCityRepository


@lru_cache(maxsize=1)
def get_city_repository() -> CityRepository:
    settings = get_settings()
    if settings.city_repository_backend == "mock":
        return MockCityRepository()

    return NormalizedCityRepository()
