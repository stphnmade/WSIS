# WSIS Data Normalization

## Canonical Geography Unit

For the MVP, WSIS uses a **city record anchored to a single county FIPS**.

Why:

- The product experience is city-first, so the UI and API should remain centered on recognizable cities.
- Most early source datasets are county-level or can be mapped cleanly to county-level geography.
- A single anchor county FIPS gives the MVP one stable join key without forcing premature multi-county metro modeling.

This means:

- `city_slug` is the product-facing stable identifier.
- `county_fips` is the canonical structured-data join key.
- The normalized dataset is one row per city anchor.

## Join Keys

- Primary structured-data join key: `county_fips`
- Product/entity key: `city_slug`
- Social placeholder compatibility key: `city_slug` with `county_fips` consistency checks

## Source Mapping

- `data/raw/simplemaps/us_cities.csv`
  - Defines the canonical city dimension and anchor county mapping.
- `data/raw/census/acs_city_metrics.csv`
  - City-level ACS inputs for income and rent.
- `data/raw/bls/county_unemployment.csv`
  - County-level labor-market input.
- `data/raw/fbi/county_crime.csv`
  - County-level crime input.
- `data/raw/noaa/county_climate.csv`
  - County-level climate input.
- `data/raw/reddit/city_sentiment.csv`
  - City-level social sentiment placeholder input.

## Processed Output

- `data/processed/city_profiles.parquet`
  - Repository-ready processed dataset used by the app by default.
- `data/raw/reddit/city_sentiment_summaries.json`
  - Structured detail-only Reddit summaries used by the city profile panel for freshness, provenance, and representative excerpts.

## TODOs

- Replace the sample raw slices with real public-source downloads and refresh logic.
- Add multi-county metro handling where city-only anchoring is too lossy.
- Add source freshness metadata and refresh jobs.

## Scope boundary

`city_profiles.parquet` is the canonical scoring table. It intentionally stores a single scalar social signal (`social_sentiment_raw`) rather than the full Reddit detail payload. Richer Reddit summaries are loaded separately at detail-view time so the scoring contract stays stable while the product can display provenance and freshness metadata.
