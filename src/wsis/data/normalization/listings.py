from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import re
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_TRACKING_PARAMETERS = {"source", "src", "ref", "referrer", "gh_src", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def _clean(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = urlencode(sorted((key, value) for key, value in parse_qsl(parts.query) if key.lower() not in _TRACKING_PARAMETERS))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


@dataclass(frozen=True)
class ListingObservation:
    source: str
    source_listing_id: str
    company_name: str
    title: str
    location_key: str
    url: str
    observed_at: datetime
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

    @property
    def dedupe_key(self) -> str:
        # Source IDs are not used alone: repositories often re-key the same job.
        identity = "|".join((_clean(self.company_name), _clean(self.title), _clean(self.location_key), canonicalize_url(self.url)))
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class ListingLifecycle:
    listing_key: str
    company_name: str
    title: str
    location_key: str
    canonical_url: str
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    source_refs: tuple[str, ...]


def deduplicate_listings(observations: Iterable[ListingObservation]) -> list[ListingLifecycle]:
    lifecycles: dict[str, ListingLifecycle] = {}
    for item in sorted(observations, key=lambda row: row.observed_at):
        key = item.dedupe_key
        ref = f"{item.source}:{item.source_listing_id}"
        current = lifecycles.get(key)
        if current is None:
            lifecycles[key] = ListingLifecycle(
                key, item.company_name, item.title, item.location_key,
                canonicalize_url(item.url), item.observed_at, item.observed_at,
                item.is_active, (ref,),
            )
            continue
        lifecycles[key] = replace(
            current,
            first_seen_at=min(current.first_seen_at, item.observed_at),
            last_seen_at=max(current.last_seen_at, item.observed_at),
            is_active=item.is_active if item.observed_at >= current.last_seen_at else current.is_active,
            source_refs=tuple(sorted(set(current.source_refs) | {ref})),
        )
    return sorted(lifecycles.values(), key=lambda row: row.listing_key)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
