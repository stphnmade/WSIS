from pathlib import Path

import pandas as pd
import pytest

from wsis.data.validation import (
    CityProfilesValidationError,
    build_city_profiles_validation_report,
    validate_city_profiles_file,
    validate_city_profiles_frame,
)


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "city_slug": "austin-tx",
                "city_name": "Austin",
                "city_name_normalized": "austin",
                "city_state_key": "austin__tx",
                "state_code": "TX",
                "state_name": "Texas",
                "county_fips": "48453",
                "county_name": "Travis County",
                "region": "South",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "population": 979882,
                "median_income": 92000,
                "median_rent": 1750,
                "fair_market_rent": 1710,
                "fair_market_rent_source": "hud_fair_market_rents_2br",
                "fair_market_rent_source_date": "2026-04-20",
                "fair_market_rent_is_imputed": False,
                "rent_to_fmr_ratio": 1.0234,
                "practical_rent_gap": 40,
                "median_home_price": 525000,
                "median_home_price_source": "cost_of_living_sample",
                "median_home_price_source_date": "2026-04-20",
                "median_home_price_is_imputed": False,
                "unemployment_pct": 3.4,
                "education_bachelors_pct": 58.0,
                "mean_commute_minutes": 25.9,
                "job_growth_pct": 4.8,
                "job_growth_source": "jobs_sample",
                "job_growth_source_date": "2026-04-20",
                "job_growth_is_imputed": False,
                "newgrad_job_post_count": 2,
                "newgrad_job_board_count": 1,
                "newgrad_job_city_page_url": "https://www.newgrad-jobs.com/entry-level-jobs/austin",
                "newgrad_jobs_source": "newgrad_jobs_local_seed",
                "newgrad_jobs_source_date": "2026-04-20",
                "newgrad_jobs_confidence": "seeded",
                "newgrad_jobs_is_imputed": True,
                "violent_crime_per_100k": 420,
                "safety_score_raw": 66,
                "avg_temp_f": 69,
                "sunny_days": 228,
                "climate_score_raw": 78,
                "social_sentiment_raw": 0.42,
                "affordability_norm": 0.62,
                "job_market_norm": 0.73,
                "safety_norm": 0.66,
                "climate_norm": 0.78,
                "social_norm": 0.71,
                "affordability_confidence": "source_backed",
                "affordability_source": "census_acs_city_metrics",
                "affordability_source_date": "2026-04-20",
                "affordability_is_imputed": False,
                "job_market_confidence": "source_backed",
                "job_market_source": "bls_county_unemployment",
                "job_market_source_date": "2026-04-20",
                "job_market_is_imputed": False,
                "safety_confidence": "source_backed",
                "safety_source": "fbi_county_crime",
                "safety_source_date": "2026-04-20",
                "safety_is_imputed": False,
                "climate_confidence": "source_backed",
                "climate_source": "noaa_county_climate",
                "climate_source_date": "2026-04-20",
                "climate_is_imputed": False,
                "social_confidence": "seeded",
                "social_source": "seeded_reddit_placeholder",
                "social_source_date": "2026-04-20",
                "social_is_imputed": False,
                "is_warm": True,
                "is_affordable": True,
                "is_high_income": True,
                "is_strong_job_market": True,
                "is_mvp_eligible": True,
                "has_simplemaps_data": True,
                "has_census_data": True,
                "has_bls_data": True,
                "has_hud_fmr_data": True,
                "has_fbi_data": True,
                "has_noaa_data": True,
                "has_reddit_data": True,
                "has_cost_of_living_context": True,
                "has_jobs_context": True,
                "has_newgrad_jobs_context": True,
                "headline": "Austin combines job resilience and positive social sentiment for early-career movers.",
                "known_for": "south, 979,882 residents, Travis County",
            }
        ]
    )


def test_validate_city_profiles_file_accepts_real_dataset() -> None:
    records = validate_city_profiles_file(Path("data/processed/city_profiles.parquet"))

    assert len(records) == 10


def test_validate_city_profiles_frame_rejects_duplicate_slugs() -> None:
    frame = pd.concat([_valid_frame(), _valid_frame()], ignore_index=True)

    with pytest.raises(CityProfilesValidationError, match="duplicate"):
        validate_city_profiles_frame(frame)


def test_validate_city_profiles_frame_rejects_null_required_fields() -> None:
    frame = _valid_frame()
    frame.loc[0, "headline"] = None

    with pytest.raises(CityProfilesValidationError, match="nulls"):
        validate_city_profiles_frame(frame)


def test_validate_city_profiles_frame_rejects_invalid_numeric_ranges() -> None:
    frame = _valid_frame()
    frame.loc[0, "social_norm"] = 1.5

    with pytest.raises(CityProfilesValidationError, match="out-of-range"):
        validate_city_profiles_frame(frame)


def test_validate_city_profiles_frame_rejects_eligible_city_with_estimated_dimension() -> None:
    frame = _valid_frame()
    frame.loc[0, "job_market_confidence"] = "estimated"

    with pytest.raises(CityProfilesValidationError, match="eligibility"):
        validate_city_profiles_frame(frame)


def test_validation_report_summarizes_coverage() -> None:
    frame = _valid_frame()

    report = build_city_profiles_validation_report(frame)

    assert report["row_count"] == 1
    assert report["eligible_city_count"] == 1
    assert report["dimension_confidence"]["social"]["seeded"] == 1
    assert report["source_coverage"]["hud_fmr"] == 1
    assert report["filter_coverage"]["is_warm"] == 1
    assert report["source_coverage"]["cost_of_living_context"] == 1
    assert report["source_coverage"]["jobs_context"] == 1
    assert report["source_coverage"]["newgrad_jobs_context"] == 1


def test_validation_report_includes_exclusion_reasons() -> None:
    frame = _valid_frame()
    frame.loc[0, "is_mvp_eligible"] = False
    frame.loc[0, "job_market_confidence"] = "estimated"

    report = build_city_profiles_validation_report(frame)

    assert "austin-tx" in report["city_exclusion_reasons"]
    assert any("job market is estimated" in reason for reason in report["city_exclusion_reasons"]["austin-tx"])


def test_validate_city_profiles_frame_rejects_invalid_filter_boolean() -> None:
    frame = _valid_frame()
    frame["is_warm"] = "yes"

    with pytest.raises(CityProfilesValidationError, match="filter booleans"):
        validate_city_profiles_frame(frame)
