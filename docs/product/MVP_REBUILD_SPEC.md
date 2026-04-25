# MVP Rebuild Spec

## Position

WSIS is relocation decision triage, not generic city ranking. The MVP helps a user decide what to do with a concrete move: pursue it, reject it, or gather missing evidence.

## Canonical users

- David is the decision user. He has a current city, a job offer, hard constraints, and soft preferences.
- Sarah is the skeptic and quality gate. She forces the product to show weak evidence, stale data, proxy assumptions, seeded context, and missing inputs.

## Required flow

1. Situation: capture baseline city, candidate city, offer, hard constraints, and soft preferences.
2. Verdict: return `Take the job`, `Viable but risky`, or `Keep looking`.
3. Evidence: show facts, confidence labels, source freshness, and exclusions.
4. Next Action: tell the user what to verify, negotiate, research, or reject.

## Decision rules

- The decision engine is the source of truth for verdicts.
- Hard constraints dominate scores and soft preferences.
- Scores can support a verdict but cannot rescue a failed hard constraint.
- Evidence must be labeled as `source_backed`, `estimated`, `seeded`, or `missing`.
- Proxy and stale evidence must be explicitly flagged.
- Social Buzz is context only and never decisive.
- Civic leaning must not be hardcoded and presented as evidence.

## MVP must remove or de-emphasize

- Map-first home
- Generic ranking claims
- Social Buzz as decisive
- Hardcoded civic leaning as real evidence
- Radar-first comparison

## MVP outputs

For each evaluated city, the product should provide:

- verdict
- hard-constraint pass/fail summary
- Chicago baseline comparison for David mode
- evidence table with confidence, freshness, and provenance
- Sarah skeptic notes
- next action

## Non-goals

- definitive best-city rankings
- live Reddit harvesting
- OAuth or persistence
- production AWS polish
- hiding weak evidence behind a single score
