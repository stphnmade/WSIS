from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CityCoverageRecord:
    place_geoid: str
    name: str
    state_code: str
    population: int | None
    available_sources: frozenset[str]
    functional_status: str = "A"


@dataclass(frozen=True)
class CitySelection:
    selected: tuple[CityCoverageRecord, ...]
    excluded_missing_population: int
    excluded_inactive: int
    excluded_missing_sources: int
    target_count: int


def select_city_universe(
    records: Iterable[CityCoverageRecord],
    required_sources: Iterable[str],
    target_count: int = 750,
    minimum_population: int = 0,
) -> CitySelection:
    """Select the largest eligible Census places with complete core coverage."""
    if target_count < 1:
        raise ValueError("target_count must be positive")
    required = frozenset(required_sources)
    eligible: list[CityCoverageRecord] = []
    missing_population = inactive = missing_sources = 0
    seen_geoids: set[str] = set()
    for record in records:
        if record.place_geoid in seen_geoids:
            raise ValueError(f"duplicate place_geoid: {record.place_geoid}")
        seen_geoids.add(record.place_geoid)
        if record.functional_status != "A":
            inactive += 1
        elif record.population is None or record.population < minimum_population:
            missing_population += 1
        elif not required.issubset(record.available_sources):
            missing_sources += 1
        else:
            eligible.append(record)
    eligible.sort(key=lambda row: (-(row.population or 0), row.state_code, row.name, row.place_geoid))
    return CitySelection(tuple(eligible[:target_count]), missing_population, inactive, missing_sources, target_count)
