# WSIS

WSIS (Where Should I Start) is a trust-first relocation decision triage tool for recent grads and first-job movers in the United States.

The current MVP helps users evaluate a concrete move, not browse a generic “best city” list. The product flow is `Situation -> Verdict -> Evidence -> Next Action`.

## MVP promise

- Evaluate David's relocation situation against a baseline city, starting with Chicago
- Apply hard constraints before any score or soft preference
- Return a clear verdict: `Take the job`, `Viable but risky`, or `Keep looking`
- Show evidence, skeptic notes, and next actions behind the verdict
- Treat social sentiment as context only
- Surface confidence and provenance so users can tell what is source-backed, estimated, seeded, or missing
- Emit a machine-readable validation report on every dataset build

## Canonical users

- David is the decision user: an early-career mover evaluating a real offer, hard budget constraints, and soft preferences against a current city.
- Sarah is the built-in skeptic and quality gate: every verdict must answer what evidence is strong, weak, stale, proxy-only, seeded, or missing.

## What the decision engine includes

The MVP decision engine may use:

- Affordability
- Job market
- Safety
- Climate
- Civic-fit proxy when sourced and labeled
- Downtown-vibe proxy when sourced and labeled

The MVP decision engine does not use:

- Social sentiment
- Hardcoded civic leaning
- Unlabeled proxy, seeded, stale, or missing evidence

Social sentiment stays visible in the product as a context panel and must not decide verdicts or rank order.

## Trust model

Confidence labels used across the dataset, API, and UI:

- `source_backed`: built from the current raw source slice without imputation for that dimension
- `estimated`: available only through fallback, imputation, or proxy treatment
- `seeded`: intentionally seeded beta context that is visible but not rank-defining
- `missing`: no usable input is available for that dimension

The UI also surfaces source freshness from file dates so stale but still source-backed slices are visible as an honesty signal without changing the ranking policy.

See [DATA_STANDARDS.md](/Users/steph/WSIS/DATA_STANDARDS.md:1) for the full policy.

## Product guardrails

- The decision engine is the source of truth for verdicts.
- Hard constraints dominate aggregate scores.
- Map-first browsing, generic ranking claims, radar-first comparison, and decisive Social Buzz are de-emphasized for MVP.
- If evidence is insufficient, the product says what is missing and gives a next action instead of forcing confidence.

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
- `WSIS_SOURCE_SAMPLE_DIR`
- `WSIS_PROCESSED_CITY_PROFILES_PATH`
- `WSIS_CITY_PROFILES_VALIDATION_REPORT_PATH`
- `WSIS_REDDIT_SENTIMENT_SUMMARIES_PATH`
- `WSIS_API_BASE_URL`
- `WSIS_SOURCE_STALE_AFTER_DAYS`

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
- [MVP_REBUILD_SPEC.md](/Users/steph/WSIS/docs/product/MVP_REBUILD_SPEC.md:1)
- [UX_SPEC.md](/Users/steph/WSIS/UX_SPEC.md:1)
- [IMPLEMENTATION_PLAN.md](/Users/steph/WSIS/IMPLEMENTATION_PLAN.md:1)
- [CITY_PROFILES_SCHEMA.md](/Users/steph/WSIS/CITY_PROFILES_SCHEMA.md:1)
- [DATA_SOURCE_MAPPINGS.md](/Users/steph/WSIS/DATA_SOURCE_MAPPINGS.md:1)
- [DATA_NORMALIZATION.md](/Users/steph/WSIS/DATA_NORMALIZATION.md:1)
- [DATA_STANDARDS.md](/Users/steph/WSIS/DATA_STANDARDS.md:1)
