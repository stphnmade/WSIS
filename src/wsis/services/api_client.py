from __future__ import annotations

from typing import Iterable

import requests

from wsis.core.config import get_settings
from wsis.domain.models import CityDetail, CitySummary, ScoreWeights
from wsis.services.city_service import CityService


class ApiCityClient:
    def __init__(self, fallback_service: CityService | None = None) -> None:
        settings = get_settings()
        self._base_url = settings.api_base_url.rstrip("/")
        self._timeout = settings.request_timeout_seconds
        self._fallback_service = fallback_service or CityService()

    def _weight_params(self, weights: ScoreWeights) -> dict[str, float]:
        return weights.model_dump()

    def list_cities(self, weights: ScoreWeights) -> tuple[list[CitySummary], str]:
        try:
            response = requests.get(
                f"{self._base_url}/api/v1/cities",
                params=self._weight_params(weights),
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            return [CitySummary.model_validate(item) for item in payload], "backend"
        except requests.RequestException:
            return self._fallback_service.list_cities(weights), "local fallback"

    def get_city(self, slug: str, weights: ScoreWeights) -> tuple[CityDetail, str]:
        try:
            response = requests.get(
                f"{self._base_url}/api/v1/cities/{slug}",
                params=self._weight_params(weights),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return CityDetail.model_validate(response.json()), "backend"
        except requests.RequestException:
            return self._fallback_service.get_city(slug, weights), "local fallback"

    def compare_cities(
        self,
        slugs: Iterable[str],
        weights: ScoreWeights,
    ) -> tuple[list[CityDetail], str]:
        slug_list = list(slugs)
        try:
            response = requests.get(
                f"{self._base_url}/api/v1/compare",
                params=[("slugs", slug) for slug in slug_list] + list(self._weight_params(weights).items()),
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            return [CityDetail.model_validate(item) for item in payload], "backend"
        except requests.RequestException:
            return self._fallback_service.compare_cities(slug_list, weights), "local fallback"

