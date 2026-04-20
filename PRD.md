# WSIS Product Requirements

## Product position

WSIS helps recent grads and first-job movers narrow a relocation shortlist honestly.

The MVP is an exploration tool, not a recommendation oracle. Its standard is practical utility with explicit data confidence, not maximum feature breadth.

## Primary job to be done

Help a young adult move from broad curiosity to a shortlist of plausible cities worth deeper research.

## MVP audience

- Recent grads
- Early-career professionals choosing a first city
- Users who need cost, jobs, safety, and climate context before committing time or money

## MVP scope

Included:

- Discovery map
- City profile
- City comparison
- Transparent score logic
- Confidence and provenance labels
- Validation-backed city dataset

Not included in MVP claims:

- Watchlist persistence
- OAuth
- AWS production deployment polish
- Live Reddit harvesting
- “Best city” or prediction-style claims

## MVP scoring policy

Ranked score includes only source-backed:

- Affordability
- Job market
- Safety
- Climate

Social sentiment is visible as context only and does not affect the score.

## MVP trust policy

- A city is eligible for ranked discovery only when affordability, job market, safety, and climate are all `source_backed`.
- Estimated or imputed core dimensions may still appear in detail view, but the city is inspection-only and excluded from ranked discovery.
- Seeded Reddit context may appear in the product, but it must be labeled `seeded` and excluded from ranking.

## Success criteria

- Users can tell what the score includes and excludes without reading code.
- Ranked results are based only on eligible, source-backed core dimensions.
- Every dataset build produces a validation report summarizing coverage and eligibility.
- The UI reflects data confidence clearly enough that a reasonable user would not mistake seeded context for ranked evidence.
