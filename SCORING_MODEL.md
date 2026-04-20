# Livability Scoring

## Ranked MVP score

The current ranked score uses only:

- affordability
- job market
- safety
- climate

Social sentiment remains visible as context only.

## Current default weights

- Affordability: 0.40
- Job market: 0.25
- Safety: 0.15
- Climate: 0.10
- Social sentiment: 0.00 for ranking

## Current scoring notes

- Affordability ranking is based on rent burden
- Job-market ranking is based on unemployment
- Safety and climate remain source-backed derived scores
- Social sentiment is still computed for context panels, but it does not affect `overall_score`
