from __future__ import annotations

from functools import lru_cache

from wsis.data.repositories.base import CityRepository
from wsis.data.repositories.factory import get_city_repository
from wsis.decision import DecisionInputs, DecisionRun, build_relocation_decisions


class DecisionRequestError(ValueError):
    """Raised when a decision request references unavailable cities."""


class DecisionService:
    def __init__(self, repository: CityRepository | None = None) -> None:
        self._repository = repository or get_city_repository()

    def run_decision(self, inputs: DecisionInputs) -> DecisionRun:
        cities = list(self._repository.list_city_metrics())
        try:
            return build_relocation_decisions(cities, inputs, dataset_count=len(cities))
        except ValueError as error:
            raise DecisionRequestError(str(error)) from error


@lru_cache(maxsize=1)
def get_decision_service() -> DecisionService:
    return DecisionService()
