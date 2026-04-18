# Canonical `city_profiles` Schema

`data/processed/city_profiles.parquet` is the canonical processed dataset used by WSIS scoring, the FastAPI backend, and the Streamlit discovery experience.

The contract is intentionally city-first:

- One row per canonical city anchor
- `city_slug` is the product-facing identifier
- `county_fips` is the structured-data join key
- Detail-only Reddit summaries are stored separately from this table so scoring stays stable

## Validation guarantees

The dataset is validated in code by [src/wsis/data/validation.py](/Users/steph/WSIS/src/wsis/data/validation.py:1) before build output is written and again when an existing parquet file is loaded.

Current checks:

- required columns must exist
- required fields cannot be null
- required string fields cannot be blank
- `city_slug` and `city_state_key` must be unique
- `county_fips` must be a 5-digit string
- `state_code` must be a 2-letter uppercase code
- numeric fields must stay inside documented ranges

## Canonical fields

| Field | Type | Required | Used by | Notes |
| --- | --- | --- | --- | --- |
| `city_slug` | string | yes | scoring, API, Streamlit | Product-facing stable identifier |
| `city_name` | string | yes | API, Streamlit | Display name |
| `city_name_normalized` | string | yes | pipeline joins | Join-safe normalized city label |
| `city_state_key` | string | yes | pipeline joins | Canonical city/state join key |
| `state_code` | string | yes | API, Streamlit | Two-letter state code |
| `state_name` | string | yes | API | Full state name |
| `county_fips` | string | yes | pipeline joins | Stable structured-data join key |
| `county_name` | string | yes | pipeline, docs | Human-readable anchor county |
| `region` | string | yes | Streamlit filters | Derived from `state_code` |
| `latitude` | float | yes | Streamlit map, API | Point geometry for current map |
| `longitude` | float | yes | Streamlit map, API | Point geometry for current map |
| `population` | integer | yes | API, Streamlit | City population from city dimension |
| `median_income` | float | yes | scoring, API, highlights | Source-backed or imputed ACS value |
| `median_rent` | float | yes | scoring, API, highlights | Source-backed or imputed ACS value |
| `median_home_price` | float | yes | scoring, API, highlights | Derived housing-value proxy |
| `unemployment_pct` | float | yes | scoring, API, highlights | Source-backed or imputed BLS value |
| `job_growth_pct` | float | yes | scoring, API, highlights | Derived proxy used until true growth series exists |
| `violent_crime_per_100k` | float | yes | API, highlights, transforms | Source-backed or imputed crime rate |
| `safety_score_raw` | float | yes | scoring, API | Derived 0-100 safety score |
| `avg_temp_f` | float | yes | API, highlights, transforms | Source-backed or imputed climate input |
| `sunny_days` | float | yes | API, highlights, transforms | Source-backed or imputed climate input |
| `climate_score_raw` | float | yes | scoring, API | Derived 0-100 climate score |
| `social_sentiment_raw` | float | yes | scoring, API | City-level normalized social sentiment input |
| `affordability_norm` | float | yes | pipeline QA, docs | 0-1 normalized affordability metric |
| `job_market_norm` | float | yes | pipeline QA, docs | 0-1 normalized job market metric |
| `safety_norm` | float | yes | pipeline QA, docs | 0-1 normalized safety metric |
| `climate_norm` | float | yes | pipeline QA, docs | 0-1 normalized climate metric |
| `social_norm` | float | yes | pipeline QA, docs | 0-1 normalized social sentiment metric |
| `has_simplemaps_data` | boolean | yes | QA | Indicates city-dimension coverage |
| `has_census_data` | boolean | yes | QA | Indicates ACS coverage before imputation |
| `has_bls_data` | boolean | yes | QA | Indicates BLS coverage before imputation |
| `has_fbi_data` | boolean | yes | QA | Indicates crime coverage before imputation |
| `has_noaa_data` | boolean | yes | QA | Indicates climate coverage before imputation |
| `has_reddit_data` | boolean | yes | QA | Indicates social sentiment score coverage before fallback |
| `headline` | string | yes | Streamlit shortlist, API | Generated city summary line |
| `known_for` | string | yes | API, fallback messaging | Generated compact descriptor |

## Range expectations

| Field | Allowed range |
| --- | --- |
| `latitude` | `[-90, 90]` |
| `longitude` | `[-180, 180]` |
| `population` | `[1, 10_000_000_000]` |
| `median_income` | `[1, 10_000_000]` |
| `median_rent` | `[1, 100_000]` |
| `median_home_price` | `[1, 100_000_000]` |
| `unemployment_pct` | `[0, 100]` |
| `job_growth_pct` | `[-100, 100]` |
| `violent_crime_per_100k` | `[0, 100_000]` |
| `safety_score_raw` | `[0, 100]` |
| `avg_temp_f` | `[-50, 150]` |
| `sunny_days` | `[0, 366]` |
| `climate_score_raw` | `[0, 100]` |
| `social_sentiment_raw` | `[-1, 1]` |
| `affordability_norm` | `[0, 1]` |
| `job_market_norm` | `[0, 1]` |
| `safety_norm` | `[0, 1]` |
| `climate_norm` | `[0, 1]` |
| `social_norm` | `[0, 1]` |

## Related contracts

- Field-level source mapping: [DATA_SOURCE_MAPPINGS.md](/Users/steph/WSIS/DATA_SOURCE_MAPPINGS.md:1)
- Normalization rules: [DATA_NORMALIZATION.md](/Users/steph/WSIS/DATA_NORMALIZATION.md:1)
- Build logic: [src/wsis/data/pipeline/city_profiles.py](/Users/steph/WSIS/src/wsis/data/pipeline/city_profiles.py:62)
