"""Pure, pipeline-independent normalization primitives for national data."""

from wsis.data.normalization.geography import (
    CBSARecord,
    LocationMatch,
    LocationMatchKind,
    PlaceRecord,
    match_location,
)
from wsis.data.normalization.listings import (
    ListingLifecycle,
    ListingObservation,
    deduplicate_listings,
)
from wsis.data.normalization.occupation import OccupationFamily, map_occupation_family
from wsis.data.normalization.quality import CityCoverageRecord, select_city_universe
from wsis.data.normalization.remote import RemoteEligibility, RemoteEligibilityStatus, parse_remote_eligibility
from wsis.data.normalization.salary import SalaryBand, SalaryPeriod, NormalizedSalary, normalize_salary, parse_salary_text
from wsis.data.normalization.unresolved import UnresolvedLocation

__all__ = [
    "CBSARecord",
    "CityCoverageRecord",
    "ListingLifecycle",
    "ListingObservation",
    "LocationMatch",
    "LocationMatchKind",
    "NormalizedSalary",
    "OccupationFamily",
    "PlaceRecord",
    "RemoteEligibility",
    "RemoteEligibilityStatus",
    "SalaryBand",
    "SalaryPeriod",
    "UnresolvedLocation",
    "deduplicate_listings",
    "map_occupation_family",
    "match_location",
    "normalize_salary",
    "parse_salary_text",
    "parse_remote_eligibility",
    "select_city_universe",
]
