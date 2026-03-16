from __future__ import annotations

from pathlib import Path

from wsis.data.models import ClimateRecord
from wsis.data.sources.base import load_csv_records


def load_climate(path: Path) -> tuple[ClimateRecord, ...]:
    return load_csv_records(path, ClimateRecord)

