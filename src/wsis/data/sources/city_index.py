from __future__ import annotations

from pathlib import Path

from wsis.data.models import CityIndexRecord
from wsis.data.sources.base import load_csv_records


def load_city_index(path: Path) -> tuple[CityIndexRecord, ...]:
    return load_csv_records(path, CityIndexRecord)

