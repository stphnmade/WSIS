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

- `data/source_samples/city_index.csv`
  - Defines the city dimension and anchor county mapping.
- `data/source_samples/cost_of_living.csv`
  - County-level affordability inputs.
- `data/source_samples/jobs.csv`
  - County-level jobs inputs.
- `data/source_samples/safety.csv`
  - County-level safety inputs.
- `data/source_samples/climate.csv`
  - County-level climate inputs.
- `data/source_samples/social_sentiment.csv`
  - City-level placeholder social input aligned to the city anchor county.

## Normalized Output

- `data/normalized/city_dataset.csv`
  - Repository-ready normalized city dataset used by the app by default.

## TODOs

- Replace sample slices with real public-source downloads and normalization logic.
- Add multi-county metro handling where city-only anchoring is too lossy.
- Add source freshness metadata and refresh jobs.

