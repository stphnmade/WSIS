from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.ingestion.bls import load_bls_unemployment
from wsis.data.ingestion.census_acs import load_census_acs
from wsis.data.ingestion.common import fill_or_default, safe_min_max
from wsis.data.ingestion.fbi import load_fbi_crime
from wsis.data.ingestion.noaa import load_noaa_climate
from wsis.data.ingestion.reddit import load_reddit_placeholder
from wsis.data.ingestion.simplemaps import load_simplemaps_cities
from wsis.data.models import CityProfileRecord


def _derive_home_price(median_rent: pd.Series) -> pd.Series:
    # TODO: replace this proxy with a real housing-value source once Zillow or ACS owner value is added.
    return (median_rent * 300).round(0)


def _derive_job_growth(unemployment_pct: pd.Series) -> pd.Series:
    # TODO: replace this proxy with a source-backed growth series when BLS growth data is wired in.
    return (7.0 - unemployment_pct).clip(lower=0.5).round(2)


def _derive_safety_score(violent_crime_per_100k: pd.Series) -> pd.Series:
    return (safe_min_max(violent_crime_per_100k, invert=True, default=0.6) * 100).round(2)


def _derive_climate_score(avg_temp_f: pd.Series, sunny_days: pd.Series) -> pd.Series:
    temp_component = 1 - ((avg_temp_f - 62).abs() / 35).clip(upper=1)
    sun_component = safe_min_max(sunny_days, invert=False, default=0.5)
    return ((temp_component * 0.55) + (sun_component * 0.45)).clip(0, 1).mul(100).round(2)


def _headline_for_row(row: pd.Series) -> str:
    traits: list[str] = []
    if row["affordability_norm"] >= 0.65:
        traits.append("relative affordability")
    if row["job_market_norm"] >= 0.65:
        traits.append("job resilience")
    if row["safety_norm"] >= 0.65:
        traits.append("safer-than-peer conditions")
    if row["climate_norm"] >= 0.65:
        traits.append("strong climate comfort")
    if row["social_norm"] >= 0.65:
        traits.append("positive social sentiment")

    if not traits:
        traits = ["a balanced relocation profile"]

    return f"{row['city_name']} combines {', '.join(traits[:3])} for early-career movers."


def _known_for_row(row: pd.Series) -> str:
    descriptors = [row["region"].lower(), f"{int(row['population']):,} residents", row["county_name"]]
    return ", ".join(descriptors)


def build_city_profiles_dataset(
    raw_root: Path | None = None,
    output_path: Path | None = None,
) -> tuple[CityProfileRecord, ...]:
    settings = get_settings()
    base_raw_root = raw_root or Path(settings.raw_data_dir)
    base_output_path = output_path or Path(settings.processed_city_profiles_path)

    city_dimension = load_simplemaps_cities(base_raw_root)
    census = load_census_acs(base_raw_root)
    bls = load_bls_unemployment(base_raw_root)
    fbi = load_fbi_crime(base_raw_root)
    noaa = load_noaa_climate(base_raw_root)
    reddit = load_reddit_placeholder(base_raw_root)

    merged = (
        city_dimension.merge(census, on=["city_state_key", "county_fips"], how="left")
        .merge(bls, on="county_fips", how="left")
        .merge(fbi, on="county_fips", how="left")
        .merge(noaa, on="county_fips", how="left")
        .merge(reddit, on="city_state_key", how="left")
    )

    for flag in [
        "has_census_data",
        "has_bls_data",
        "has_fbi_data",
        "has_noaa_data",
        "has_reddit_data",
    ]:
        if flag not in merged.columns:
            merged[flag] = False
        merged[flag] = merged[flag].map(lambda value: bool(value) if pd.notna(value) else False)

    merged["median_income"] = fill_or_default(merged.get("median_income"), 75000)
    merged["median_rent"] = fill_or_default(merged.get("median_rent"), 1550)
    merged["unemployment_pct"] = fill_or_default(merged.get("unemployment_pct"), 4.0)
    merged["violent_crime_per_100k"] = fill_or_default(merged.get("violent_crime_per_100k"), 380)
    merged["avg_temp_f"] = fill_or_default(merged.get("avg_temp_f"), 60)
    merged["sunny_days"] = fill_or_default(merged.get("sunny_days"), 205)
    merged["social_sentiment_raw"] = fill_or_default(merged.get("social_sentiment_raw"), 0.0).clip(-1, 1)

    merged["median_home_price"] = _derive_home_price(merged["median_rent"])
    merged["job_growth_pct"] = _derive_job_growth(merged["unemployment_pct"])
    merged["safety_score_raw"] = _derive_safety_score(merged["violent_crime_per_100k"])
    merged["climate_score_raw"] = _derive_climate_score(merged["avg_temp_f"], merged["sunny_days"])

    rent_burden = (merged["median_rent"] * 12) / merged["median_income"]
    home_price_ratio = merged["median_home_price"] / merged["median_income"]
    merged["affordability_norm"] = (
        (safe_min_max(rent_burden, invert=True, default=0.5) * 0.7)
        + (safe_min_max(home_price_ratio, invert=True, default=0.5) * 0.3)
    ).round(4)
    merged["job_market_norm"] = (
        safe_min_max(merged["job_growth_pct"], invert=False, default=0.5) * 0.55
        + safe_min_max(merged["unemployment_pct"], invert=True, default=0.5) * 0.45
    ).round(4)
    merged["safety_norm"] = (merged["safety_score_raw"] / 100).round(4)
    merged["climate_norm"] = (merged["climate_score_raw"] / 100).round(4)
    merged["social_norm"] = (((merged["social_sentiment_raw"] + 1) / 2).clip(0, 1)).round(4)

    merged["headline"] = merged.apply(_headline_for_row, axis=1)
    merged["known_for"] = merged.apply(_known_for_row, axis=1)

    output_columns = [
        "city_slug",
        "city_name",
        "city_name_normalized",
        "city_state_key",
        "state_code",
        "state_name",
        "county_fips",
        "county_name",
        "region",
        "latitude",
        "longitude",
        "population",
        "median_income",
        "median_rent",
        "median_home_price",
        "unemployment_pct",
        "job_growth_pct",
        "violent_crime_per_100k",
        "safety_score_raw",
        "avg_temp_f",
        "sunny_days",
        "climate_score_raw",
        "social_sentiment_raw",
        "affordability_norm",
        "job_market_norm",
        "safety_norm",
        "climate_norm",
        "social_norm",
        "has_simplemaps_data",
        "has_census_data",
        "has_bls_data",
        "has_fbi_data",
        "has_noaa_data",
        "has_reddit_data",
        "headline",
        "known_for",
    ]

    processed = merged[output_columns].sort_values(["state_code", "city_name"]).reset_index(drop=True)
    base_output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.to_parquet(base_output_path, index=False)

    return tuple(CityProfileRecord.model_validate(record) for record in processed.to_dict("records"))


def main() -> None:
    records = build_city_profiles_dataset()
    print(f"Built city_profiles dataset with {len(records)} records.")


if __name__ == "__main__":
    main()
