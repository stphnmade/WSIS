from __future__ import annotations

from pathlib import Path

from wsis.data.models import SafetyRecord
from wsis.data.sources.base import load_csv_records


def load_safety(path: Path) -> tuple[SafetyRecord, ...]:
    return load_csv_records(path, SafetyRecord)

