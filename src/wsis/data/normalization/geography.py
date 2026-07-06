from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata
from typing import Iterable


STATE_CODE_PATTERN = re.compile(r"\b([A-Z]{2})\b")
PLACE_SUFFIX_PATTERN = re.compile(
    r"\s+(city|town|village|borough|municipality|cdp|balance)$", re.IGNORECASE
)


class LocationMatchKind(str, Enum):
    PLACE = "place"
    CBSA = "cbsa"
    REMOTE = "remote"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class PlaceRecord:
    place_geoid: str
    name: str
    state_code: str
    cbsa_code: str | None = None
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{7}", self.place_geoid):
            raise ValueError("place_geoid must contain seven digits")
        if not re.fullmatch(r"[A-Z]{2}", self.state_code):
            raise ValueError("state_code must be a two-letter USPS code")


@dataclass(frozen=True)
class CBSARecord:
    cbsa_code: str
    name: str
    principal_place_geoids: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{5}", self.cbsa_code):
            raise ValueError("cbsa_code must contain five digits")


@dataclass(frozen=True)
class LocationMatch:
    raw_location: str
    kind: LocationMatchKind
    normalized_label: str
    place_geoid: str | None = None
    cbsa_code: str | None = None
    state_code: str | None = None
    confidence: str = "unknown"
    matched_by: str = "none"


def normalize_location_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = PLACE_SUFFIX_PATTERN.sub("", ascii_value.strip())
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _split_city_state(raw: str) -> tuple[str, str | None]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    state = None
    if len(parts) >= 2:
        match = STATE_CODE_PATTERN.search(parts[-1].upper())
        if match:
            state = match.group(1)
    return parts[0] if parts else raw.strip(), state


def match_location(
    raw_location: str,
    places: Iterable[PlaceRecord],
    cbsas: Iterable[CBSARecord] = (),
) -> LocationMatch:
    """Resolve a source label to a Census place first, then a CBSA.

    Ambiguous names without an explicit state remain unresolved instead of being
    assigned to an arbitrary place.
    """
    raw = raw_location.strip()
    normalized_raw = normalize_location_name(raw)
    if re.search(r"\b(remote|anywhere|work from home)\b", normalized_raw):
        return LocationMatch(raw, LocationMatchKind.REMOTE, "remote", confidence="source_backed", matched_by="remote_keyword")

    city, state = _split_city_state(raw)
    city_key = normalize_location_name(city)
    candidates: list[tuple[PlaceRecord, str]] = []
    for place in places:
        keys = {normalize_location_name(place.name)}
        keys.update(normalize_location_name(alias) for alias in place.aliases)
        if city_key in keys and (state is None or place.state_code == state):
            candidates.append((place, "canonical_name" if city_key == normalize_location_name(place.name) else "alias"))
    if len(candidates) == 1:
        place, matched_by = candidates[0]
        return LocationMatch(
            raw, LocationMatchKind.PLACE, f"{place.name}, {place.state_code}",
            place_geoid=place.place_geoid, cbsa_code=place.cbsa_code,
            state_code=place.state_code, confidence="source_backed", matched_by=matched_by,
        )

    cbsa_candidates: list[tuple[CBSARecord, str]] = []
    for cbsa in cbsas:
        keys = {normalize_location_name(cbsa.name)}
        keys.update(normalize_location_name(alias) for alias in cbsa.aliases)
        if normalized_raw in keys or city_key in keys:
            cbsa_candidates.append((cbsa, "canonical_name" if normalized_raw == normalize_location_name(cbsa.name) else "alias"))
    if len(cbsa_candidates) == 1:
        cbsa, matched_by = cbsa_candidates[0]
        return LocationMatch(
            raw, LocationMatchKind.CBSA, cbsa.name, cbsa_code=cbsa.cbsa_code,
            state_code=state, confidence="source_backed", matched_by=matched_by,
        )
    return LocationMatch(raw, LocationMatchKind.UNRESOLVED, normalized_raw, state_code=state)
