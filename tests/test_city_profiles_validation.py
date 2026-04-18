from pathlib import Path

import pandas as pd
import pytest

from wsis.data.validation import (
    CityProfilesValidationError,
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
                "median_home_price": 525000,
                "unemployment_pct": 3.4,
                "job_growth_pct": 4.8,
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
                "has_simplemaps_data": True,
                "has_census_data": True,
                "has_bls_data": True,
                "has_fbi_data": True,
                "has_noaa_data": True,
                "has_reddit_data": True,
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
