import pandas as pd

from scripts.audit_national_job_coverage import build_coverage


def test_job_coverage_matches_census_place_and_alias() -> None:
    places = pd.DataFrame([
        {"place_geoid": "0667000", "place_name": "San Francisco city", "state_code": "CA", "functional_status": "A", "lsad_code": "25"},
        {"place_geoid": "4805000", "place_name": "Austin city", "state_code": "TX", "functional_status": "A", "lsad_code": "25"},
    ])
    listings = [
        {"id": "1", "active": True, "is_visible": True, "locations": ["SF, CA"], "date_updated": 1},
        {"id": "2", "active": True, "is_visible": True, "locations": ["Austin, TX"], "date_updated": 2},
        {"id": "3", "active": False, "is_visible": True, "locations": ["Austin, TX"], "date_updated": 3},
        {"id": "4", "active": True, "is_visible": True, "locations": ["London, UK"], "date_updated": 4},
    ]

    coverage, report = build_coverage(places, listings)

    assert set(coverage["place_geoid"]) == {"0667000", "4805000"}
    assert coverage["active_listing_count"].sum() == 2
    assert report["active_source_listing_count"] == 3
    assert report["matched_place_count"] == 2
    assert report["parseable_us_location_count"] == 2
