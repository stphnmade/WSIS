from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import load_raw_csv


def load_noaa_climate(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "noaa" / "county_climate.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(columns=["county_fips", "avg_temp_f", "sunny_days", "has_noaa_data"])

    standardized = frame.copy()
    standardized["has_noaa_data"] = True
    return standardized[["county_fips", "avg_temp_f", "sunny_days", "has_noaa_data"]]

