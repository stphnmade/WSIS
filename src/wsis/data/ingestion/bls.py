from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import load_raw_csv


def load_bls_unemployment(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "bls" / "county_unemployment.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(columns=["county_fips", "unemployment_pct", "has_bls_data"])

    standardized = frame.copy()
    standardized["has_bls_data"] = True
    return standardized[["county_fips", "unemployment_pct", "has_bls_data"]]

