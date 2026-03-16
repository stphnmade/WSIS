from __future__ import annotations

from pathlib import Path

from wsis.data.models import CostOfLivingRecord
from wsis.data.sources.base import load_csv_records


def load_cost_of_living(path: Path) -> tuple[CostOfLivingRecord, ...]:
    return load_csv_records(path, CostOfLivingRecord)

