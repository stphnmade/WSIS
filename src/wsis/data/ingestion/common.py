from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pandas as pd


STATE_TO_REGION = {
    "AL": "South",
    "AK": "West",
    "AZ": "West",
    "AR": "South",
    "CA": "West",
    "CO": "West",
    "CT": "Northeast",
    "DE": "South",
    "FL": "South",
    "GA": "South",
    "HI": "West",
    "IA": "Midwest",
    "ID": "West",
    "IL": "Midwest",
    "IN": "Midwest",
    "KS": "Midwest",
    "KY": "South",
    "LA": "South",
    "MA": "Northeast",
    "MD": "South",
    "ME": "Northeast",
    "MI": "Midwest",
    "MN": "Midwest",
    "MO": "Midwest",
    "MS": "South",
    "MT": "West",
    "NC": "South",
    "ND": "Midwest",
    "NE": "Midwest",
    "NH": "Northeast",
    "NJ": "Northeast",
    "NM": "West",
    "NV": "West",
    "NY": "Northeast",
    "OH": "Midwest",
    "OK": "South",
    "OR": "West",
    "PA": "Northeast",
    "RI": "Northeast",
    "SC": "South",
    "SD": "Midwest",
    "TN": "South",
    "TX": "South",
    "UT": "West",
    "VA": "South",
    "VT": "Northeast",
    "WA": "West",
    "WI": "Midwest",
    "WV": "South",
    "WY": "West",
}


def normalize_city_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def build_city_state_key(city_name: str, state_code: str) -> str:
    return f"{normalize_city_name(city_name)}__{state_code.lower()}"


def build_city_slug(city_name: str, state_code: str) -> str:
    return f"{normalize_city_name(city_name).replace(' ', '-')}-{state_code.lower()}"


def load_raw_csv(path: Path, dtype: dict[str, Any] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=dtype)


def safe_min_max(series: pd.Series, invert: bool = False, default: float = 0.5) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series([default] * len(series), index=series.index, dtype="float64")

    minimum = numeric.min()
    maximum = numeric.max()
    if minimum == maximum:
        return pd.Series([default] * len(series), index=series.index, dtype="float64")

    normalized = (numeric - minimum) / (maximum - minimum)
    if invert:
        normalized = 1 - normalized
    return normalized.fillna(default).clip(0, 1)


def fill_or_default(series: pd.Series, default: float) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series([default] * len(series), index=series.index, dtype="float64")
    return numeric.fillna(numeric.median()).fillna(default)

