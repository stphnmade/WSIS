from __future__ import annotations

import json
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
from wsis.domain.models import ALL_DIMENSIONS, ConfidenceLabel, RANKED_DIMENSIONS


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


def _require_confidence_metadata(frame: pd.DataFrame) -> None:
    valid_confidences = set(ConfidenceLabel.__args__)
    failures: list[str] = []

    for dimension in ALL_DIMENSIONS:
        confidence_column = f"{dimension}_confidence"
        source_column = f"{dimension}_source"
        source_date_column = f"{dimension}_source_date"
        imputed_column = f"{dimension}_is_imputed"

        invalid_confidence = ~frame[confidence_column].astype("string").isin(valid_confidences)
        if invalid_confidence.any():
            examples = frame.loc[invalid_confidence, confidence_column].astype(str).head(5).tolist()
            failures.append(f"{confidence_column} invalid={examples}")

        if frame[source_column].astype("string").str.strip().eq("").any():
            failures.append(f"{source_column} contains blank values")

        if frame[source_date_column].astype("string").str.strip().eq("").any():
            failures.append(f"{source_date_column} contains blank values")

        source_backed_imputed = frame[confidence_column].eq("source_backed") & frame[imputed_column]
        if source_backed_imputed.any():
            examples = frame.loc[source_backed_imputed, "city_slug"].astype(str).head(5).tolist()
            failures.append(f"{dimension} marks source_backed while imputed for {examples}")

    if failures:
        _raise("city_profiles contains invalid confidence metadata: " + "; ".join(failures))


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


def _require_mvp_eligibility_consistency(frame: pd.DataFrame) -> None:
    eligible = frame[frame["is_mvp_eligible"]]
    if eligible.empty:
        return

    failures: list[str] = []
    for dimension in RANKED_DIMENSIONS:
        confidence_column = f"{dimension}_confidence"
        imputed_column = f"{dimension}_is_imputed"
        invalid = eligible[confidence_column].ne("source_backed") | eligible[imputed_column]
        if invalid.any():
            slugs = eligible.loc[invalid, "city_slug"].astype(str).tolist()
            failures.append(f"{dimension} not fully source_backed for eligible cities {slugs}")

    if failures:
        _raise("city_profiles violates MVP eligibility rules: " + "; ".join(failures))


def build_city_profiles_validation_report(
    frame: pd.DataFrame,
    dataset_path: Path | None = None,
) -> dict[str, object]:
    report: dict[str, object] = {
        "dataset_path": str(dataset_path) if dataset_path is not None else "",
        "row_count": int(len(frame)),
        "eligible_city_count": int(frame["is_mvp_eligible"].sum()),
        "ineligible_city_count": int((~frame["is_mvp_eligible"]).sum()),
        "cities_excluded_from_mvp": sorted(
            frame.loc[~frame["is_mvp_eligible"], "city_slug"].astype(str).tolist()
        ),
        "dimension_confidence": {},
        "dimension_imputation": {},
        "source_coverage": {
            "simplemaps": int(frame["has_simplemaps_data"].sum()),
            "census": int(frame["has_census_data"].sum()),
            "bls": int(frame["has_bls_data"].sum()),
            "fbi": int(frame["has_fbi_data"].sum()),
            "noaa": int(frame["has_noaa_data"].sum()),
            "reddit": int(frame["has_reddit_data"].sum()),
        },
        "failures": [],
    }

    for dimension in ALL_DIMENSIONS:
        confidence_column = f"{dimension}_confidence"
        imputed_column = f"{dimension}_is_imputed"
        confidence_counts = (
            frame[confidence_column].astype("string").value_counts(dropna=False).sort_index()
        )
        report["dimension_confidence"][dimension] = {
            str(label): int(count) for label, count in confidence_counts.items()
        }
        report["dimension_imputation"][dimension] = {
            "imputed_count": int(frame[imputed_column].sum()),
            "imputed_pct": round(float(frame[imputed_column].mean() * 100), 2),
        }

    return report


def write_city_profiles_validation_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def validate_city_profiles_frame(frame: pd.DataFrame) -> tuple[CityProfileRecord, ...]:
    _require_columns(frame)
    _require_no_nulls(frame)
    _require_non_empty_strings(frame)
    _require_no_duplicates(frame)
    _require_confidence_metadata(frame)
    _require_identifier_formats(frame)
    _require_numeric_ranges(frame)
    _require_mvp_eligibility_consistency(frame)
    return tuple(CityProfileRecord.model_validate(record) for record in frame.to_dict("records"))


def validate_city_profiles_file(path: Path) -> tuple[CityProfileRecord, ...]:
    frame = pd.read_parquet(path)
    return validate_city_profiles_frame(frame)


def main() -> None:
    settings = get_settings()
    path = Path(settings.processed_city_profiles_path)
    report_path = Path(settings.city_profiles_validation_report_path)
    frame = pd.read_parquet(path)
    records = validate_city_profiles_frame(frame)
    report = build_city_profiles_validation_report(frame, path)
    write_city_profiles_validation_report(report, report_path)
    print(
        "Validated city_profiles dataset with "
        f"{len(records)} records at {path}. Report: {report_path}."
    )


if __name__ == "__main__":
    main()
