# Canonical `city_profiles` Schema

`data/processed/city_profiles.parquet` is the canonical processed dataset used by scoring, the API, and Streamlit.

The table remains city-first:

- one row per canonical city anchor
- `city_slug` is the product-facing identifier
- `county_fips` is the structured-data join key

## Core guarantees

Validation enforces:

- required columns exist
- required fields are non-null and non-blank
- identity columns are unique
- numeric fields remain in expected ranges
- confidence metadata is present and valid
- any city marked `is_mvp_eligible=true` has source-backed, non-imputed affordability, job market, safety, and climate dimensions

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

## Current semantics

- `social_confidence` is currently `seeded` when local placeholder social data exists
- `is_mvp_eligible` is based only on the four ranked core dimensions
- the validation report for each build is written to `data/processed/city_profiles_validation_report.json`
