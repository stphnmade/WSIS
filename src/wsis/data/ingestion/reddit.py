from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.data.ingestion.common import build_city_state_key, load_raw_csv


def load_reddit_sentiment(raw_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(raw_root / "reddit" / "city_sentiment.csv", dtype={"county_fips": str})
    if frame.empty:
        return pd.DataFrame(columns=["city_state_key", "social_sentiment_raw", "has_reddit_data"])

    standardized = frame.copy()
    standardized["city_state_key"] = standardized.apply(
        lambda row: build_city_state_key(row["city"], row["state_id"]),
        axis=1,
    )
    standardized["has_reddit_data"] = True
    return standardized[["city_state_key", "social_sentiment_raw", "has_reddit_data"]]


load_reddit_placeholder = load_reddit_sentiment
