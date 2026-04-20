# WSIS Data Normalization

## Canonical geography

For the MVP, WSIS uses one city record anchored to one county FIPS.

- `city_slug` is the product-facing key
- `county_fips` is the structured-data join key

## Ranked normalization policy

The ranked MVP score uses:

- affordability from rent burden against local median income
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

## Output artifacts

- `data/processed/city_profiles.parquet`
- `data/processed/city_profiles_validation_report.json`
