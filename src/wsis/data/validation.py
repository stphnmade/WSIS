from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.models import (
    CITY_PROFILE_NON_EMPTY_STRING_COLUMNS,
    CITY_PROFILE_RANGE_RULES,
    CITY_PROFILE_REQUIRED_COLUMNS,
    CITY_PROFILE_UNIQUE_COLUMNS,
    CityProfileRecord,
)


class CityProfilesValidationError(ValueError):
    """Raised when the canonical city_profiles dataset fails data quality checks."""


def _raise(message: str) -> None:
    raise CityProfilesValidationError(message)


def _require_columns(frame: pd.DataFrame) -> None:
    missing = sorted(set(CITY_PROFILE_REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        _raise(f"city_profiles is missing required columns: {', '.join(missing)}")


def _require_no_nulls(frame: pd.DataFrame) -> None:
    null_counts = {
        column: int(frame[column].isna().sum())
        for column in CITY_PROFILE_REQUIRED_COLUMNS
        if frame[column].isna().any()
    }
    if null_counts:
        details = ", ".join(f"{column}={count}" for column, count in sorted(null_counts.items()))
        _raise(f"city_profiles contains nulls in required columns: {details}")


def _require_non_empty_strings(frame: pd.DataFrame) -> None:
    blank_counts = {}
    for column in CITY_PROFILE_NON_EMPTY_STRING_COLUMNS:
        series = frame[column].astype("string")
        blank_mask = series.isna() | series.str.strip().eq("")
        if blank_mask.any():
            blank_counts[column] = int(blank_mask.sum())

    if blank_counts:
        details = ", ".join(f"{column}={count}" for column, count in sorted(blank_counts.items()))
        _raise(f"city_profiles contains blank required strings: {details}")


def _require_no_duplicates(frame: pd.DataFrame) -> None:
    duplicates = {}
    for column in CITY_PROFILE_UNIQUE_COLUMNS:
        duplicate_mask = frame.duplicated(subset=[column], keep=False)
        if duplicate_mask.any():
            values = frame.loc[duplicate_mask, column].astype(str).drop_duplicates().tolist()
            duplicates[column] = values[:5]

    if duplicates:
        details = ", ".join(
            f"{column}={values}" for column, values in sorted(duplicates.items())
        )
        _raise(f"city_profiles contains duplicate identity values: {details}")


def _require_identifier_formats(frame: pd.DataFrame) -> None:
    county_fips_mask = ~frame["county_fips"].astype("string").str.fullmatch(r"\d{5}", na=False)
    if county_fips_mask.any():
        examples = frame.loc[county_fips_mask, "county_fips"].astype(str).head(5).tolist()
        _raise(f"city_profiles contains invalid county_fips values: {examples}")

    state_code_mask = ~frame["state_code"].astype("string").str.fullmatch(r"[A-Z]{2}", na=False)
    if state_code_mask.any():
        examples = frame.loc[state_code_mask, "state_code"].astype(str).head(5).tolist()
        _raise(f"city_profiles contains invalid state_code values: {examples}")

    slug_pattern = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*-[a-z]{2}$")
    slug_mask = ~frame["city_slug"].astype("string").map(
        lambda value: bool(slug_pattern.fullmatch(str(value)))
    )
    if slug_mask.any():
        examples = frame.loc[slug_mask, "city_slug"].astype(str).head(5).tolist()
        _raise(f"city_profiles contains invalid city_slug values: {examples}")


def _require_numeric_ranges(frame: pd.DataFrame) -> None:
    failures: list[str] = []
    for column, (minimum, maximum) in CITY_PROFILE_RANGE_RULES.items():
        series = pd.to_numeric(frame[column], errors="coerce")
        invalid = series.isna() | (series < minimum) | (series > maximum)
        if invalid.any():
            examples = frame.loc[invalid, column].astype(str).head(3).tolist()
            failures.append(f"{column} outside [{minimum}, {maximum}] examples={examples}")

    if failures:
        _raise("city_profiles contains out-of-range numeric values: " + "; ".join(failures))


def validate_city_profiles_frame(frame: pd.DataFrame) -> tuple[CityProfileRecord, ...]:
    _require_columns(frame)
    _require_no_nulls(frame)
    _require_non_empty_strings(frame)
    _require_no_duplicates(frame)
    _require_identifier_formats(frame)
    _require_numeric_ranges(frame)
    return tuple(CityProfileRecord.model_validate(record) for record in frame.to_dict("records"))


def validate_city_profiles_file(path: Path) -> tuple[CityProfileRecord, ...]:
    frame = pd.read_parquet(path)
    return validate_city_profiles_frame(frame)


def main() -> None:
    settings = get_settings()
    path = Path(settings.processed_city_profiles_path)
    records = validate_city_profiles_file(path)
    print(f"Validated city_profiles dataset with {len(records)} records at {path}.")


if __name__ == "__main__":
    main()
