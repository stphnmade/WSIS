from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class UnresolvedLocation:
    source: str
    source_record_id: str
    raw_location: str
    normalized_location: str
    reason: str
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int = 1
    candidate_place_geoids: tuple[str, ...] = ()
    candidate_cbsa_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.first_seen_at.tzinfo is None or self.last_seen_at.tzinfo is None:
            raise ValueError("queue timestamps must be timezone-aware")
        if self.last_seen_at < self.first_seen_at:
            raise ValueError("last_seen_at cannot precede first_seen_at")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["first_seen_at"] = self.first_seen_at.isoformat()
        record["last_seen_at"] = self.last_seen_at.isoformat()
        record["candidate_place_geoids"] = list(self.candidate_place_geoids)
        record["candidate_cbsa_codes"] = list(self.candidate_cbsa_codes)
        return record
