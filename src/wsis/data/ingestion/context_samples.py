from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import load_raw_csv


def load_cost_of_living_context(source_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(source_root / "cost_of_living.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "county_fips",
                "median_home_price",
                "has_cost_of_living_context",
            ]
        )

    standardized = frame.copy()
    standardized["has_cost_of_living_context"] = True
    return standardized[["county_fips", "median_home_price", "has_cost_of_living_context"]]


def load_jobs_context(source_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(source_root / "jobs.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "county_fips",
                "job_growth_pct",
                "has_jobs_context",
            ]
        )

    standardized = frame.copy()
    standardized["has_jobs_context"] = True
    return standardized[["county_fips", "job_growth_pct", "has_jobs_context"]]
