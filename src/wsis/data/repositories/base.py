from __future__ import annotations

from typing import Protocol

from wsis.domain.models import CityMetrics


class CityRepository(Protocol):
    def list_city_metrics(self) -> tuple[CityMetrics, ...]:
        """Return repository-backed city metrics for the current environment."""

