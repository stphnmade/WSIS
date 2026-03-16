from __future__ import annotations

from pathlib import Path

from wsis.data.models import JobsRecord
from wsis.data.sources.base import load_csv_records


def load_jobs(path: Path) -> tuple[JobsRecord, ...]:
    return load_csv_records(path, JobsRecord)

