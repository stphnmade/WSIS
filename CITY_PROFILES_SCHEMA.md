# city_profiles Schema

`data/processed/city_profiles.parquet` is the canonical processed dataset for WSIS.

## Identity and joins

- `city_slug`: product-facing stable city identifier
- `city_name`: display city name
- `city_name_normalized`: normalized join-safe city name
- `city_state_key`: canonical city/state join key for city-shaped sources
- `state_code`, `state_name`
- `county_fips`, `county_name`: canonical structured-data join key
- `region`

## Location and scale

- `latitude`, `longitude`
- `population`

## Raw or source-backed metrics

- `median_income`
- `median_rent`
- `unemployment_pct`
- `violent_crime_per_100k`
- `avg_temp_f`
- `sunny_days`
- `social_sentiment_raw`

## Derived compatibility metrics

- `median_home_price`
  - Derived from rent as a housing-value proxy until a housing price source is added.
- `job_growth_pct`
  - Derived from unemployment as a short-term compatibility proxy until a true growth series is added.
- `safety_score_raw`
  - Derived from crime-rate normalization.
- `climate_score_raw`
  - Derived from temperature comfort and sunny-day counts.

## Normalized metrics

All normalized metrics are on a 0-1 scale:

- `affordability_norm`
- `job_market_norm`
- `safety_norm`
- `climate_norm`
- `social_norm`

## Data availability flags

- `has_simplemaps_data`
- `has_census_data`
- `has_bls_data`
- `has_fbi_data`
- `has_noaa_data`
- `has_reddit_data`

These flags allow the app to stay runnable when optional sources are missing.

## Product compatibility fields

- `headline`
- `known_for`

These are generated placeholders so the existing UI contract stays intact.

