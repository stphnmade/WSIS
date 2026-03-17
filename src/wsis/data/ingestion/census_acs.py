from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import build_city_state_key, load_raw_csv


def load_census_acs(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "census" / "acs_city_metrics.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(columns=["city_state_key", "county_fips", "median_income", "median_rent", "has_census_data"])

    standardized = frame.copy()
    standardized["city_state_key"] = standardized.apply(
        lambda row: build_city_state_key(row["city"], row["state_id"]),
        axis=1,
    )
    standardized["has_census_data"] = True
    return standardized[["city_state_key", "county_fips", "median_income", "median_rent", "has_census_data"]]

