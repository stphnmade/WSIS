# WSIS Data Normalization

## Canonical geography

For the MVP, WSIS uses one city record anchored to one county FIPS.

- `city_slug` is the product-facing key
- `county_fips` is the structured-data join key

## Ranked normalization policy

The ranked MVP score uses:

- affordability from rent burden against local median income plus HUD fair-market-rent context
- job market from unemployment conditions
- safety from the current crime-rate slice
- climate from the current climate slice

The ranked MVP score does not use social sentiment.

## Confidence policy

Each ranked or contextual dimension carries:

- confidence label
- source name
- source date
- imputation flag

These fields are part of the canonical dataset, not UI-only decorations.

## Core Public Reliable Feed v1

Normalized raw inputs are expected in local CSV form so the app keeps running when external refreshes fail:

- Census ACS 5-Year: median income, median rent, population, education, commute
- BLS LAUS: unemployment rate
- HUD Fair Market Rents: practical rent affordability
- NOAA Climate Normals: climate inputs

If a public feed or row is missing, the pipeline falls back to local seed/default values and marks the affected dimension or field as estimated/imputed.

## Filter fields

The canonical dataset materializes:

- `is_warm`
- `is_affordable`
- `is_high_income`
- `is_strong_job_market`

## Output artifacts

- `data/processed/city_profiles.parquet`
- `data/processed/city_profiles_validation_report.json`
