from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import build_city_state_key, load_raw_csv


def load_census_acs(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "census" / "acs_city_metrics.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "city_state_key",
                "county_fips",
                "acs_population",
                "median_income",
                "median_rent",
                "education_bachelors_pct",
                "mean_commute_minutes",
                "has_census_data",
            ]
        )

    standardized = frame.copy()
    standardized = standardized.rename(
        columns={
            "population": "acs_population",
            "bachelors_degree_pct": "education_bachelors_pct",
            "commute_minutes": "mean_commute_minutes",
        }
    )
    standardized["city_state_key"] = standardized.apply(
        lambda row: build_city_state_key(row["city"], row["state_id"]),
        axis=1,
    )
    standardized["has_census_data"] = True
    for optional_column in [
        "acs_population",
        "education_bachelors_pct",
        "mean_commute_minutes",
    ]:
        if optional_column not in standardized.columns:
            standardized[optional_column] = pd.NA

    return standardized[
        [
            "city_state_key",
            "county_fips",
            "acs_population",
            "median_income",
            "median_rent",
            "education_bachelors_pct",
            "mean_commute_minutes",
            "has_census_data",
        ]
    ]
