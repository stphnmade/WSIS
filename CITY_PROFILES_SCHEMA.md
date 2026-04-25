# Canonical `city_profiles` Schema

`data/processed/city_profiles.parquet` is the canonical processed dataset used by scoring, the API, and Streamlit.

The table remains city-first:

- one row per canonical city anchor
- `city_slug` is the product-facing identifier
- `county_fips` is the structured-data join key
- public-feed v1 keeps normalized source slices in `data/raw/*` and local seed files in the same shape

## Core guarantees

Validation enforces:

- required columns exist
- required fields are non-null and non-blank
- identity columns are unique
- numeric fields remain in expected ranges
- confidence metadata is present and valid
- any city marked `is_mvp_eligible=true` has source-backed, non-imputed affordability, job market, safety, and climate dimensions
- filter-ready boolean columns are materialized as booleans

## Trust fields

Per-dimension metadata stored in the table:

- `*_confidence`
- `*_source`
- `*_source_date`
- `*_is_imputed`

Dimensions covered:

- `affordability`
- `job_market`
- `safety`
- `climate`
- `social`

Eligibility field:

- `is_mvp_eligible`

Filter-ready fields:

- `is_warm`
- `is_affordable`
- `is_high_income`
- `is_strong_job_market`

Public-feed v1 context fields:

- `fair_market_rent`, `rent_to_fmr_ratio`, `practical_rent_gap`
- `education_bachelors_pct`, `mean_commute_minutes`
- `fair_market_rent_*` source and imputation metadata

## Current semantics

- `social_confidence` is currently `seeded` when local placeholder social data exists
- `is_mvp_eligible` is based only on the four ranked core dimensions
- `affordability_confidence` requires both ACS rent/income and HUD FMR coverage
- ACS population overrides the city dimension population when present; SimpleMaps remains the geography fallback
- the validation report for each build is written to `data/processed/city_profiles_validation_report.json`
