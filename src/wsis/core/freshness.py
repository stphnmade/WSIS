from __future__ import annotations

from datetime import date, datetime


def parse_source_date(value: str) -> date | None:
    if not value or value == "unknown":
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def source_age_days(value: str, today: date | None = None) -> int | None:
    parsed = parse_source_date(value)
    if parsed is None:
        return None
    anchor = today or date.today()
    return max((anchor - parsed).days, 0)


def source_freshness_label(
    value: str,
    stale_after_days: int,
    today: date | None = None,
) -> str:
    age_days = source_age_days(value, today=today)
    if age_days is None:
        return "unknown"
    if age_days > stale_after_days:
        return "stale"
    if age_days > max(int(stale_after_days * 0.5), 30):
        return "aging"
    return "current"
