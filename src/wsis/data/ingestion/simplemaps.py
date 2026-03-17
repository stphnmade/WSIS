from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import (
    STATE_TO_REGION,
    build_city_slug,
    build_city_state_key,
    load_raw_csv,
    normalize_city_name,
)


def load_simplemaps_cities(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "simplemaps" / "us_cities.csv", dtype={"county_fips": str})
    if frame.empty:
        raise FileNotFoundError("SimpleMaps raw file is required to define the city dimension.")

    standardized = frame.rename(
        columns={
            "city": "city_name",
            "state_id": "state_code",
            "state_name": "state_name",
            "lat": "latitude",
            "lng": "longitude",
        }
    ).copy()
    standardized["city_name_normalized"] = standardized["city_name"].map(normalize_city_name)
    standardized["city_state_key"] = standardized.apply(
        lambda row: build_city_state_key(row["city_name"], row["state_code"]),
        axis=1,
    )
    standardized["city_slug"] = standardized.apply(
        lambda row: build_city_slug(row["city_name"], row["state_code"]),
        axis=1,
    )
    standardized["region"] = standardized["state_code"].map(STATE_TO_REGION).fillna("Unknown")
    standardized["has_simplemaps_data"] = True

    columns = [
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
        "has_simplemaps_data",
    ]
    return standardized[columns].drop_duplicates(subset=["city_state_key"])

