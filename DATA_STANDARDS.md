# WSIS Data Standards

## Purpose

These standards define when WSIS may treat a city as trustworthy enough for ranked MVP discovery.

## Confidence labels

### `source_backed`

- The dimension is built from the current raw source slice for that city or county anchor
- No imputation is required for that dimension
- The dimension may participate in ranked MVP scoring

### `estimated`

- The dimension depends on fallback values, imputation, or proxy treatment
- The dimension may remain visible in detail view
- The dimension must not support ranked MVP eligibility claims

### `seeded`

- The data is intentionally pre-seeded beta context rather than a fully trusted source-backed feed
- The dimension may appear in the UI only when clearly labeled
- The dimension must not affect the ranked MVP score

### `missing`

- No usable value is available
- The dimension cannot participate in ranked MVP scoring

## MVP eligibility rule

A city is eligible for ranked discovery only if these four dimensions are all `source_backed`:

- Affordability
- Job market
- Safety
- Climate

If any one of those dimensions is `estimated` or `missing`, the city remains inspection-only.

## Current social policy

- Social sentiment is currently beta context
- It is labeled `seeded` when available from the local placeholder pipeline
- It is excluded from ranked scoring
