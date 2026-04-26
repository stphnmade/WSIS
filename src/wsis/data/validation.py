from __future__ import annotations

import json
from pathlib import Path
import re

import pandas as pd

from wsis.core.freshness import source_age_days, source_freshness_label
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


FILTER_BOOLEAN_COLUMNS = (
    "is_warm",
    "is_affordable",
    "is_high_income",
    "is_strong_job_market",
    "has_newgrad_jobs_context",
)


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


def _require_filter_booleans(frame: pd.DataFrame) -> None:
    failures: list[str] = []
    for column in FILTER_BOOLEAN_COLUMNS:
        if column not in frame.columns:
            failures.append(f"{column} missing")
            continue
        if not pd.api.types.is_bool_dtype(frame[column]):
            examples = frame[column].astype(str).head(5).tolist()
            failures.append(f"{column} must be boolean examples={examples}")

    if failures:
        _raise("city_profiles contains invalid filter booleans: " + "; ".join(failures))


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


def _exclusion_reasons(frame: pd.DataFrame) -> dict[str, list[str]]:
    reasons: dict[str, list[str]] = {}
    ineligible = frame.loc[~frame["is_mvp_eligible"]]
    for _, row in ineligible.iterrows():
        city_reasons: list[str] = []
        for dimension in RANKED_DIMENSIONS:
            confidence = str(row[f"{dimension}_confidence"])
            if confidence != "source_backed":
                city_reasons.append(
                    f"{dimension.replace('_', ' ')} is {confidence} from {row[f'{dimension}_source']}"
                )
        reasons[str(row["city_slug"])] = city_reasons
    return reasons


def _source_file_status(
    frame: pd.DataFrame,
    raw_root: Path,
    source_samples_root: Path,
    stale_after_days: int,
) -> dict[str, dict[str, object]]:
    source_specs = {
        "simplemaps": (raw_root / "simplemaps" / "us_cities.csv", "has_simplemaps_data"),
        "census": (raw_root / "census" / "acs_city_metrics.csv", "has_census_data"),
        "bls": (raw_root / "bls" / "county_unemployment.csv", "has_bls_data"),
        "hud_fmr": (raw_root / "hud" / "fair_market_rents.csv", "has_hud_fmr_data"),
        "fbi": (raw_root / "fbi" / "county_crime.csv", "has_fbi_data"),
        "noaa": (raw_root / "noaa" / "county_climate.csv", "has_noaa_data"),
        "reddit": (raw_root / "reddit" / "city_sentiment.csv", "has_reddit_data"),
        "cost_of_living_context": (
            source_samples_root / "cost_of_living.csv",
            "has_cost_of_living_context",
        ),
        "jobs_context": (source_samples_root / "jobs.csv", "has_jobs_context"),
        "newgrad_jobs_context": (
            source_samples_root / "newgrad_jobs.csv",
            "has_newgrad_jobs_context",
        ),
    }
    status: dict[str, dict[str, object]] = {}
    row_count = max(len(frame), 1)
    for source_name, (path, coverage_column) in source_specs.items():
        exists = path.exists()
        source_date = (
            pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").date().isoformat()
            if exists
            else "unknown"
        )
        coverage_count = int(frame[coverage_column].sum()) if coverage_column in frame.columns else 0
        coverage_pct = round((coverage_count / row_count) * 100, 2)
        age_days = source_age_days(source_date)
        freshness = source_freshness_label(source_date, stale_after_days)
        status_value = "healthy"
        if not exists:
            status_value = "missing"
        elif coverage_count == 0:
            status_value = "outage"
        elif coverage_count < len(frame):
            status_value = "partial_outage"

        status[source_name] = {
            "path": str(path),
            "exists": exists,
            "source_date": source_date,
            "age_days": age_days,
            "freshness": freshness,
            "coverage_count": coverage_count,
            "coverage_pct": coverage_pct,
            "status": status_value,
        }
    return status


def build_city_profiles_validation_report(
    frame: pd.DataFrame,
    dataset_path: Path | None = None,
    raw_root: Path | None = None,
    source_samples_root: Path | None = None,
) -> dict[str, object]:
    settings = get_settings()
    resolved_raw_root = raw_root or Path(settings.raw_data_dir)
    resolved_source_samples_root = source_samples_root or Path(settings.source_samples_dir)
    source_status = _source_file_status(
        frame,
        resolved_raw_root,
        resolved_source_samples_root,
        settings.source_stale_after_days,
    )
    stale_sources = sorted(
        source_name
        for source_name, status in source_status.items()
        if status["freshness"] == "stale"
    )
    partial_outages = sorted(
        source_name
        for source_name, status in source_status.items()
        if status["status"] in {"partial_outage", "outage", "missing"}
    )
    report: dict[str, object] = {
        "dataset_path": str(dataset_path) if dataset_path is not None else "",
        "row_count": int(len(frame)),
        "eligible_city_count": int(frame["is_mvp_eligible"].sum()),
        "ineligible_city_count": int((~frame["is_mvp_eligible"]).sum()),
        "cities_excluded_from_mvp": sorted(
            frame.loc[~frame["is_mvp_eligible"], "city_slug"].astype(str).tolist()
        ),
        "city_exclusion_reasons": _exclusion_reasons(frame),
        "dimension_confidence": {},
        "dimension_imputation": {},
        "source_coverage": {
            "simplemaps": int(frame["has_simplemaps_data"].sum()),
            "census": int(frame["has_census_data"].sum()),
            "bls": int(frame["has_bls_data"].sum()),
            "hud_fmr": int(frame["has_hud_fmr_data"].sum()),
            "fbi": int(frame["has_fbi_data"].sum()),
            "noaa": int(frame["has_noaa_data"].sum()),
            "reddit": int(frame["has_reddit_data"].sum()),
            "cost_of_living_context": int(frame["has_cost_of_living_context"].sum()),
            "jobs_context": int(frame["has_jobs_context"].sum()),
            "newgrad_jobs_context": int(frame["has_newgrad_jobs_context"].sum()),
        },
        "source_file_status": source_status,
        "stale_sources": stale_sources,
        "partial_outages": partial_outages,
        "filter_coverage": {
            column: int(frame[column].sum()) for column in FILTER_BOOLEAN_COLUMNS
        },
        "failures": [
            *[f"stale source: {source_name}" for source_name in stale_sources],
            *[f"source coverage issue: {source_name}" for source_name in partial_outages],
        ],
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
    _require_filter_booleans(frame)
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
    report = build_city_profiles_validation_report(
        frame,
        path,
        raw_root=Path(settings.raw_data_dir),
        source_samples_root=Path(settings.source_samples_dir),
    )
    write_city_profiles_validation_report(report, report_path)
    print(
        "Validated city_profiles dataset with "
        f"{len(records)} records at {path}. Report: {report_path}."
    )


if __name__ == "__main__":
    main()
