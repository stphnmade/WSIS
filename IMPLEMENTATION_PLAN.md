# Implementation Plan

## Phase 1

Decision contract

- Define Situation, Verdict, Evidence, and Next Action response shapes
- Make the decision engine the source of truth for verdicts
- Model David as the canonical decision user and Chicago as his required baseline
- Add Sarah-style skeptic notes for weak, stale, proxy-only, seeded, or missing evidence

## Phase 2

Trust-first data contract

- Add per-dimension confidence, provenance, freshness, and imputation metadata
- Add eligibility flags for confident verdicts and inspection-only results
- Emit a machine-readable validation report during dataset builds
- Flag seeded, proxy, stale, and missing evidence wherever it can affect interpretation

## Phase 3

Hard constraints and verdict semantics

- Apply hard constraints before aggregate scores or soft preferences
- Return `Take the job`, `Viable but risky`, or `Keep looking`
- Say directly when no city satisfies David's rent target
- Exclude social sentiment and hardcoded civic leaning from verdict logic

## Phase 4

Decision-first UI alignment

- Rework the primary flow around `Situation -> Verdict -> Evidence -> Next Action`
- De-emphasize map-first home, generic ranking claims, radar-first comparison, and decisive Social Buzz
- Show Sarah-style skeptic notes next to weak evidence
- Keep setup, API, and Streamlit flows environment-variable driven

## Phase 5

Source depth and validation hardening

- Replace remaining hardcoded, proxy, or fallback logic where practical
- Add sourced civic-fit and downtown-vibe proxy data
- Tighten coverage thresholds
- Expand QA around dataset freshness and provenance
