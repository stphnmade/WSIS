# WSIS

WSIS (Where Should I Start) is a map-first relocation discovery product for young adults and early-career professionals in the United States. This milestone delivers a local-first vertical slice with a FastAPI backend, a Streamlit frontend, a transparent scoring model, and a normalized city dataset built from source-shaped sample slices.

## What is included

- FastAPI service scaffold with health, city list, city detail, and comparison endpoints
- Streamlit app with a discovery map, city profile view, and comparison view
- Shared typed domain models, config module, scoring engine, and service layer
- Canonical city dataset built from source adapters under `data/source_samples/`
- Repository abstraction so the app can switch between normalized and mock data cleanly
- Placeholder Reddit sentiment service interface with deterministic mock output

## Project structure

```text
apps/
  api/main.py
  streamlit/Home.py
  streamlit/pages/
data/
  normalized/city_dataset.csv
  source_samples/
src/
  wsis/
    api/
    core/
    data/
      pipeline/
      repositories/
      sources/
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

By default the app uses the normalized repository backend defined in `.env.example`.

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

Source sample files:

- `data/source_samples/city_index.csv`
- `data/source_samples/cost_of_living.csv`
- `data/source_samples/jobs.csv`
- `data/source_samples/safety.csv`
- `data/source_samples/climate.csv`
- `data/source_samples/social_sentiment.csv`

Normalized output:

- `data/normalized/city_dataset.csv`

Rebuild the normalized dataset locally:

```bash
python -m wsis.data.pipeline.normalize
```

Reference documentation:

- `DATA_NORMALIZATION.md`

## Current scoring model

Default weights from the product docs:

- Affordability: 0.40
- Job market: 0.25
- Safety: 0.15
- Climate: 0.10
- Social sentiment: 0.10

The current engine reads repository-backed city metrics from the normalized dataset and still applies transparent min-max normalization within the active city cohort.

## Deferred integrations

- Real city ingest and normalization pipelines from Census, BLS, crime, climate, and housing sources
- Real external downloads and richer transforms behind the current sample source adapters
- GeoPandas-based choropleth polygons once the canonical city geometry pipeline is ready
- Real Reddit harvesting, entity resolution, summarization, and moderation logic
- Postgres or Supabase persistence
- AWS containerization and deployment assets

## Validation

Recommended local checks:

```bash
python3 -m compileall src apps tests
python3 -m pytest
```

## Notes for the next milestone

- Replace the sample slices with real source downloads and refreshable normalization jobs
- Add a Postgres-backed repository behind the existing city repository interface
- Introduce batch jobs for scoring refresh and Reddit panel refresh
- Add deployment assets for Lambda container images and ECR
