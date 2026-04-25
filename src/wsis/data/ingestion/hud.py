from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import load_raw_csv


def load_hud_fair_market_rents(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "hud" / "fair_market_rents.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "county_fips",
                "fair_market_rent",
                "hud_area_name",
                "has_hud_fmr_data",
            ]
        )

    standardized = frame.rename(
        columns={
            "fmr_2br": "fair_market_rent",
            "fair_market_rent_2br": "fair_market_rent",
            "area_name": "hud_area_name",
        }
    ).copy()
    if "hud_area_name" not in standardized.columns:
        standardized["hud_area_name"] = "unknown"
    standardized["has_hud_fmr_data"] = True
    return standardized[
        [
            "county_fips",
            "fair_market_rent",
            "hud_area_name",
            "has_hud_fmr_data",
        ]
    ]
