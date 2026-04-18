# Field-Level Source Mappings

This document explains where each canonical `city_profiles` field comes from and what assumptions WSIS currently makes when transforming raw inputs into product-ready city metrics.

## Identity and geography

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `city_slug` | `data/raw/simplemaps/us_cities.csv` | Derived from normalized city name + state code |
| `city_name` | `data/raw/simplemaps/us_cities.csv` | Passed through as display name |
| `city_name_normalized` | `data/raw/simplemaps/us_cities.csv` | Lowercased and punctuation-normalized for joins |
| `city_state_key` | `data/raw/simplemaps/us_cities.csv` | Derived as `<normalized city>__<state_code>` |
| `state_code` | `data/raw/simplemaps/us_cities.csv` | Two-letter code from city dimension |
| `state_name` | `data/raw/simplemaps/us_cities.csv` | Passed through |
| `county_fips` | `data/raw/simplemaps/us_cities.csv` | Canonical join key for county-shaped sources |
| `county_name` | `data/raw/simplemaps/us_cities.csv` | Passed through |
| `region` | `state_code` + in-code region map | Derived using `STATE_TO_REGION` in [src/wsis/data/ingestion/common.py](/Users/steph/WSIS/src/wsis/data/ingestion/common.py:10) |
| `latitude`, `longitude` | `data/raw/simplemaps/us_cities.csv` | Current point geometry for map plotting |
| `population` | `data/raw/simplemaps/us_cities.csv` | Passed through as the city-scale population value |

## Economic inputs

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `median_income` | `data/raw/census/acs_city_metrics.csv` | Coerced numeric; missing values filled with source median, then default `75000` |
| `median_rent` | `data/raw/census/acs_city_metrics.csv` | Coerced numeric; missing values filled with source median, then default `1550` |
| `unemployment_pct` | `data/raw/bls/county_unemployment.csv` | County-level value mapped by `county_fips`; missing values filled with source median, then default `4.0` |
| `job_growth_pct` | derived | Proxy only: `7.0 - unemployment_pct`, clipped at `0.5` |

## Safety and climate inputs

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `violent_crime_per_100k` | `data/raw/fbi/county_crime.csv` | County-level rate mapped by `county_fips`; missing values filled with source median, then default `380` |
| `safety_score_raw` | derived from `violent_crime_per_100k` | Inverted min-max scaling to 0-100 inside the current build cohort |
| `avg_temp_f` | `data/raw/noaa/county_climate.csv` | County-level value mapped by `county_fips`; missing values filled with source median, then default `60` |
| `sunny_days` | `data/raw/noaa/county_climate.csv` | County-level value mapped by `county_fips`; missing values filled with source median, then default `205` |
| `climate_score_raw` | derived from `avg_temp_f` and `sunny_days` | Temperature comfort centered around `62F`, combined with sunshine using a `55/45` split, then scaled to 0-100 |

## Social sentiment

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `social_sentiment_raw` | `data/raw/reddit/city_sentiment.csv` | City-level input clipped to `[-1, 1]`; scoring uses this canonical scalar only |
| `social_norm` | derived from `social_sentiment_raw` | Transformed to `[0, 1]` by `(raw + 1) / 2` |
| Detail-view Reddit panel | `data/raw/reddit/city_sentiment_summaries.json` | Separate structured payload for summaries, provenance, freshness, and representative excerpts; not used by scoring |

## Derived affordability and scoring inputs

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `median_home_price` | derived from `median_rent` | Housing-value proxy: `median_rent * 300` |
| `affordability_norm` | derived | Blend of inverted rent burden (`70%`) and inverted home-price ratio (`30%`) |
| `job_market_norm` | derived | Blend of positive job-growth scaling (`55%`) and inverted unemployment scaling (`45%`) |
| `safety_norm` | derived | `safety_score_raw / 100` |
| `climate_norm` | derived | `climate_score_raw / 100` |

## Availability and product-facing fields

| Field | Source | Transformation / assumption |
| --- | --- | --- |
| `has_simplemaps_data` | pipeline flag | `True` when city-dimension row exists |
| `has_census_data` | pipeline flag | Indicates ACS join coverage before imputation |
| `has_bls_data` | pipeline flag | Indicates BLS join coverage before imputation |
| `has_fbi_data` | pipeline flag | Indicates FBI join coverage before imputation |
| `has_noaa_data` | pipeline flag | Indicates NOAA join coverage before imputation |
| `has_reddit_data` | pipeline flag | Indicates scalar Reddit sentiment coverage before fallback |
| `headline` | derived | Generated from normalized strengths above threshold `0.65` |
| `known_for` | derived | Compact descriptor built from region, population, and county name |

## Important current assumptions

- WSIS is still a city-anchor model, not a full metro model.
- Several fields are intentionally proxies until richer sources are wired in.
- County-shaped inputs are attached to one anchor county per city, which is a simplification for metros spanning multiple counties.
- The Reddit detail panel is credible-looking structured content, but it is still seeded/precomputed local data rather than a live ingestion pipeline.
