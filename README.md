# WSIS

WSIS (Where Should I Start) is a trust-first relocation exploration tool for recent grads and first-job movers in the United States.

The current MVP helps users narrow a shortlist honestly. It does not claim to produce a definitive “best city” ranking.

## MVP promise

- Explore a balanced-middle city set with a map, profile view, and comparison flow
- Rank cities only when affordability, job market, safety, and climate are source-backed
- Show social sentiment as context only
- Surface confidence and provenance so users can tell what is source-backed, estimated, seeded, or missing
- Emit a machine-readable validation report on every dataset build

## What the current score includes

The ranked MVP score includes:

- Affordability
- Job market
- Safety
- Climate

The ranked MVP score does not include:

- Social sentiment

Social sentiment stays visible in the product as a seeded beta context panel and does not change rank order.

## Trust model

Confidence labels used across the dataset, API, and UI:

- `source_backed`: built from the current raw source slice without imputation for that dimension
- `estimated`: available only through fallback, imputation, or proxy treatment
- `seeded`: intentionally seeded beta context that is visible but not rank-defining
- `missing`: no usable input is available for that dimension

See [DATA_STANDARDS.md](/Users/steph/WSIS/DATA_STANDARDS.md:1) for the full policy.

## Project structure

```text
apps/
  api/main.py
  streamlit/Home.py
  streamlit/pages/
data/
  raw/
  processed/city_profiles.parquet
  processed/city_profiles_validation_report.json
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

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Environment-driven paths:

- `WSIS_RAW_DATA_DIR`
- `WSIS_PROCESSED_CITY_PROFILES_PATH`
- `WSIS_CITY_PROFILES_VALIDATION_REPORT_PATH`
- `WSIS_REDDIT_SENTIMENT_SUMMARIES_PATH`
- `WSIS_API_BASE_URL`

## Run the backend

```bash
uvicorn apps.api.main:app --reload
```

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`

## Run the frontend

```bash
streamlit run apps/streamlit/Home.py
```

- Streamlit app: `http://localhost:8501/`

The frontend prefers the FastAPI backend when available and falls back to the local shared service when the backend is offline.

## Build and validate the dataset

Build the canonical dataset and validation report:

```bash
python3 -m wsis.data.pipeline.city_profiles
```

Validate the current processed dataset:

```bash
python3 -m wsis.data.validation
```

Build artifacts:

- `data/processed/city_profiles.parquet`
- `data/processed/city_profiles_validation_report.json`

## Local checks

```bash
python3 -m wsis.data.validation
python3 -m compileall src apps tests
python3 -m pytest -q
```

## Reference docs

- [PRD.md](/Users/steph/WSIS/PRD.md:1)
- [UX_SPEC.md](/Users/steph/WSIS/UX_SPEC.md:1)
- [IMPLEMENTATION_PLAN.md](/Users/steph/WSIS/IMPLEMENTATION_PLAN.md:1)
- [CITY_PROFILES_SCHEMA.md](/Users/steph/WSIS/CITY_PROFILES_SCHEMA.md:1)
- [DATA_SOURCE_MAPPINGS.md](/Users/steph/WSIS/DATA_SOURCE_MAPPINGS.md:1)
- [DATA_NORMALIZATION.md](/Users/steph/WSIS/DATA_NORMALIZATION.md:1)
- [DATA_STANDARDS.md](/Users/steph/WSIS/DATA_STANDARDS.md:1)
