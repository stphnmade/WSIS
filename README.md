# WSIS

WSIS (Where Should I Start) is a map-first relocation discovery product for young adults and early-career professionals in the United States. This milestone delivers a local-first vertical slice with a FastAPI backend, a Streamlit frontend, a transparent scoring model, and a modular ingestion pipeline that produces a canonical `city_profiles` dataset from public-source-shaped raw files.

## What is included

- FastAPI service scaffold with health, city list, city detail, and comparison endpoints
- Streamlit app with a discovery map, city profile view, and comparison view
- Shared typed domain models, config module, scoring engine, and service layer
- Canonical `city_profiles` dataset built from raw source adapters under `data/raw/`
- Repository abstraction so the app can switch between processed and mock data cleanly
- Structured Reddit sentiment detail adapter with precomputed freshness and provenance metadata

## Project structure

```text
apps/
  api/main.py
  streamlit/Home.py
  streamlit/pages/
data/
  raw/
  processed/city_profiles.parquet
src/
  wsis/
    api/
    core/
    data/
      ingestion/
      pipeline/
      repositories/
    domain/
    scoring/
    services/
tests/
```

## Local setup

1. Create a virtual environment.
2. Install the package in editable mode.
3. Copy `.env.example` to `.env` if you want local overrides.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

By default the app uses the processed `city_profiles` repository backend defined in `.env.example`.

Optional detail-only Reddit summary payload:

- `WSIS_REDDIT_SENTIMENT_SUMMARIES_PATH=data/raw/reddit/city_sentiment_summaries.json`

## Run the backend

```bash
uvicorn apps.api.main:app --reload
```

Backend URLs:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`

## Run the frontend

In a second terminal:

```bash
source .venv/bin/activate
streamlit run apps/streamlit/Home.py
```

Frontend URL:

- Streamlit app: `http://localhost:8501/`

The frontend prefers the FastAPI backend when it is available at `WSIS_API_BASE_URL`. If the backend is offline, it falls back to the shared local service so the prototype still runs.

## Data pipeline

Canonical MVP geography:

- One city record anchored to one `county_fips`
- `county_fips` is the structured-data join key
- `city_slug` remains the product-facing identifier

This keeps the product city-first while using a stable join key across county-shaped source data.

Raw input files:

- `data/raw/simplemaps/us_cities.csv`
- `data/raw/census/acs_city_metrics.csv`
- `data/raw/bls/county_unemployment.csv`
- `data/raw/fbi/county_crime.csv`
- `data/raw/noaa/county_climate.csv`
- `data/raw/reddit/city_sentiment.csv`
- `data/raw/reddit/city_sentiment_summaries.json`

Processed output:

- `data/processed/city_profiles.parquet`

Build the processed dataset locally:

```bash
python -m wsis.data.pipeline.city_profiles
```

Reference documentation:

- `DATA_NORMALIZATION.md`
- `CITY_PROFILES_SCHEMA.md`
- `DATA_SOURCE_MAPPINGS.md`

## Current scoring model

Default weights from the product docs:

- Affordability: 0.40
- Job market: 0.25
- Safety: 0.15
- Climate: 0.10
- Social sentiment: 0.10

The current engine reads repository-backed city metrics from `city_profiles.parquet` and still applies transparent min-max normalization within the active city cohort.

City profile Reddit detail panels are loaded separately from a structured precomputed summary file so scoring remains stable while the UI can show freshness, methodology, and provenance metadata.

## Deferred integrations

- Real public-source downloads and refreshable ingestion jobs
- Stronger source-specific transforms, QA checks, and provenance metadata
- GeoPandas-based choropleth polygons once the canonical city geometry pipeline is ready
- Real Reddit harvesting, entity resolution, summarization, and moderation logic
- Postgres or Supabase persistence
- AWS containerization and deployment assets

## Validation

Recommended local checks:

```bash
python3 -m wsis.data.validation
python3 -m compileall src apps tests
python3 -m pytest
```

## Notes for the next milestone

- Replace the sample raw slices with real public-source downloads and refreshable ingestion jobs
- Add a Postgres-backed repository behind the existing city repository interface
- Introduce batch jobs for scoring refresh and Reddit panel refresh
- Add deployment assets for Lambda container images and ECR
