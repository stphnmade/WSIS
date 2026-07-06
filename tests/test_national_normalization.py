from datetime import datetime, timezone

import pytest

from wsis.data.normalization.geography import (
    CBSARecord,
    LocationMatchKind,
    PlaceRecord,
    match_location,
)
from wsis.data.normalization.listings import ListingObservation, canonicalize_url, deduplicate_listings
from wsis.data.normalization.occupation import OccupationFamily, map_occupation_family
from wsis.data.normalization.quality import CityCoverageRecord, select_city_universe
from wsis.data.normalization.remote import RemoteEligibilityStatus, parse_remote_eligibility
from wsis.data.normalization.salary import SalaryBand, SalaryPeriod, normalize_salary, parse_salary_text
from wsis.data.normalization.unresolved import UnresolvedLocation


PLACES = (
    PlaceRecord("0667000", "San Francisco city", "CA", "41860", ("SF",)),
    PlaceRecord("2954074", "Oakland city", "MO", None),
    PlaceRecord("0653000", "Oakland city", "CA", "41860"),
)
CBSAS = (CBSARecord("41860", "San Francisco-Oakland-Berkeley, CA", ("0667000", "0653000"), ("Bay Area",)),)


def test_location_matches_place_alias_with_state() -> None:
    match = match_location("SF, CA", PLACES, CBSAS)
    assert match.kind is LocationMatchKind.PLACE
    assert match.place_geoid == "0667000"
    assert match.cbsa_code == "41860"
    assert match.matched_by == "alias"


def test_location_does_not_guess_ambiguous_place() -> None:
    match = match_location("Oakland", PLACES, CBSAS)
    assert match.kind is LocationMatchKind.UNRESOLVED


def test_location_matches_cbsa_alias_and_remote() -> None:
    assert match_location("Bay Area", PLACES, CBSAS).cbsa_code == "41860"
    assert match_location("Remote - US", PLACES, CBSAS).kind is LocationMatchKind.REMOTE


def test_remote_states_are_confirmed_only_when_explicit() -> None:
    confirmed = parse_remote_eligibility("Remote: California, NY, or Texas")
    assert confirmed.status is RemoteEligibilityStatus.CONFIRMED
    assert confirmed.eligible_state_codes == ("CA", "NY", "TX")
    unknown = parse_remote_eligibility(["Remote", "United States"])
    assert unknown.status is RemoteEligibilityStatus.UNKNOWN
    assert unknown.eligible_state_codes == ()
    assert parse_remote_eligibility("Austin, TX").status is RemoteEligibilityStatus.NOT_REMOTE


def test_salary_normalizes_period_range_and_band() -> None:
    salary = normalize_salary(40, 50, SalaryPeriod.HOUR)
    assert (salary.annual_min, salary.annual_max) == (83_200, 104_000)
    assert salary.band is SalaryBand.FROM_90K_TO_130K
    assert salary.confidence == "source_backed"


def test_salary_handles_reversed_or_non_usd_values() -> None:
    salary = normalize_salary(10_000, 8_000, SalaryPeriod.MONTH, "cad")
    assert (salary.annual_min, salary.annual_max) == (96_000, 120_000)
    assert salary.confidence == "unconverted_currency"
    assert normalize_salary(None, None).band is SalaryBand.UNKNOWN


def test_salary_parses_common_source_text() -> None:
    annual = parse_salary_text("$80k - $100K / year")
    assert (annual.annual_min, annual.annual_max) == (80_000, 100_000)
    hourly = parse_salary_text("$42.50 per hour")
    assert (hourly.annual_min, hourly.annual_max) == (88_400, 88_400)


@pytest.mark.parametrize(
    ("title", "family"),
    [
        ("Software Engineer", OccupationFamily.TECH),
        ("Senior Data Analyst", OccupationFamily.DATA),
        ("Product Manager", OccupationFamily.PRODUCT),
        ("UX Designer", OccupationFamily.DESIGN),
        ("Business Operations Associate", OccupationFamily.OPERATIONS),
        ("Growth Marketing Manager", OccupationFamily.MARKETING),
        ("Federal Government Affairs Analyst", OccupationFamily.FEDERAL),
        ("Staff Attorney", OccupationFamily.OTHER),
    ],
)
def test_occupation_family_scaffolding(title: str, family: OccupationFamily) -> None:
    assert map_occupation_family(title).family is family


def test_federal_is_preserved_as_sector_without_fake_soc_code() -> None:
    mapping = map_occupation_family("Federal Civil Service Analyst")
    assert mapping.family is OccupationFamily.FEDERAL
    assert mapping.soc_family_codes == ()
    assert mapping.confidence == "sector_keyword"


def test_listing_dedupe_tracks_sources_and_lifecycle() -> None:
    first = datetime(2026, 7, 1, tzinfo=timezone.utc)
    last = datetime(2026, 7, 3, tzinfo=timezone.utc)
    observations = [
        ListingObservation("board_a", "1", "Acme, Inc.", "Data Analyst", "0667000", "https://jobs.acme.test/1?utm_source=a", first),
        ListingObservation("board_b", "xyz", "Acme Inc", "Data Analyst", "0667000", "https://jobs.acme.test/1?ref=b", last, False),
    ]
    rows = deduplicate_listings(observations)
    assert len(rows) == 1
    assert rows[0].first_seen_at == first
    assert rows[0].last_seen_at == last
    assert rows[0].is_active is False
    assert rows[0].source_refs == ("board_a:1", "board_b:xyz")
    assert canonicalize_url(observations[0].url) == "https://jobs.acme.test/1"


def test_listing_rejects_naive_observation_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ListingObservation("source", "1", "Acme", "Engineer", "remote", "", datetime(2026, 7, 1))


def test_unresolved_queue_has_json_ready_format() -> None:
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)
    item = UnresolvedLocation("jobs", "12", "Portland", "portland", "ambiguous_place", now, now, candidate_place_geoids=("4159000",))
    record = item.to_record()
    assert record["first_seen_at"] == "2026-07-04T00:00:00+00:00"
    assert record["candidate_place_geoids"] == ["4159000"]


def test_city_quality_gate_requires_population_status_and_sources() -> None:
    records = [
        CityCoverageRecord("0000001", "Large", "AA", 1_000_000, frozenset({"census", "jobs"})),
        CityCoverageRecord("0000002", "Small", "BB", 50_000, frozenset({"census", "jobs"})),
        CityCoverageRecord("0000003", "Missing Jobs", "CC", 2_000_000, frozenset({"census"})),
        CityCoverageRecord("0000004", "No Population", "DD", None, frozenset({"census", "jobs"})),
        CityCoverageRecord("0000005", "Inactive", "EE", 3_000_000, frozenset({"census", "jobs"}), "I"),
    ]
    result = select_city_universe(records, {"census", "jobs"}, target_count=1)
    assert [row.name for row in result.selected] == ["Large"]
    assert result.excluded_missing_sources == 1
    assert result.excluded_missing_population == 1
    assert result.excluded_inactive == 1


def test_city_quality_gate_rejects_duplicate_geoids() -> None:
    record = CityCoverageRecord("0000001", "One", "AA", 1, frozenset())
    with pytest.raises(ValueError, match="duplicate place_geoid"):
        select_city_universe([record, record], set())
