# Implementation Plan

## Phase 1

Trust-first data contract

- Add per-dimension confidence, provenance, and imputation metadata
- Add MVP eligibility flag for ranked discovery
- Emit a machine-readable validation report during dataset builds

## Phase 2

Trust-first scoring and API semantics

- Rank only eligible cities
- Exclude social sentiment from the ranked score
- Expose score context, confidence labels, and inclusion/exclusion metadata through the API

## Phase 3

Trust-first UI alignment

- Update map, profile, and comparison views to explain score inclusion rules
- Surface confidence, provenance, and beta warnings
- Keep social context visible without letting it influence rank

## Phase 4

Source depth and validation hardening

- Replace remaining proxy or fallback logic where practical
- Tighten coverage thresholds
- Expand QA around dataset freshness and provenance
