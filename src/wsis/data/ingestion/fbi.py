from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import load_raw_csv


def load_fbi_crime(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "fbi" / "county_crime.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(columns=["county_fips", "violent_crime_per_100k", "has_fbi_data"])

    standardized = frame.copy()
    standardized["has_fbi_data"] = True
    return standardized[["county_fips", "violent_crime_per_100k", "has_fbi_data"]]

