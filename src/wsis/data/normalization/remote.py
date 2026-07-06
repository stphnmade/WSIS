from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable


class RemoteEligibilityStatus(str, Enum):
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"
    NOT_REMOTE = "not_remote"


@dataclass(frozen=True)
class RemoteEligibility:
    is_remote: bool
    status: RemoteEligibilityStatus
    eligible_state_codes: tuple[str, ...] = ()
    evidence: str = ""


_STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}
_VALID_CODES = frozenset(_STATE_NAMES.values())


def _extract_states(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    states = {code for name, code in _STATE_NAMES.items() if re.search(rf"\b{re.escape(name)}\b", lowered)}
    # Preserve case so ordinary words such as "or" are not interpreted as OR.
    states.update(code for code in re.findall(r"\b[A-Z]{2}\b", text) if code in _VALID_CODES)
    return tuple(sorted(states))


def parse_remote_eligibility(
    locations: str | Iterable[str],
    description: str = "",
) -> RemoteEligibility:
    values = [locations] if isinstance(locations, str) else list(locations)
    evidence = " | ".join(str(value) for value in values if value)
    combined = f"{evidence} {description}".strip()
    is_remote = bool(re.search(r"\b(remote|anywhere|work from home|wfh)\b", combined, re.IGNORECASE))
    if not is_remote:
        return RemoteEligibility(False, RemoteEligibilityStatus.NOT_REMOTE, evidence=evidence)
    states = _extract_states(combined)
    if states:
        return RemoteEligibility(True, RemoteEligibilityStatus.CONFIRMED, states, evidence)
    return RemoteEligibility(True, RemoteEligibilityStatus.UNKNOWN, evidence=evidence)
