# WSIS Product Requirements

## Product position

WSIS helps recent grads and first-job movers triage a relocation decision honestly.

The MVP is not a generic city ranking, map browser, or recommendation oracle. Its standard is decision usefulness: show whether a move is plausible, why, what evidence is weak, and what the user should do next.

## Primary job to be done

Help a young adult evaluate a concrete relocation situation and decide whether to pursue it, reject it, or gather missing evidence.

## MVP audience

- David: the canonical decision user. David has a specific job offer, a current baseline city, hard affordability constraints, and soft preferences.
- Sarah: the built-in skeptic and quality gate. Sarah represents the questions a careful reviewer would ask before trusting a verdict: What is hard evidence? What is stale, missing, seeded, or proxy-only? What would change the answer?
- Secondary users: recent grads and early-career movers with a similar concrete relocation decision.

## MVP scope

Included:

- Situation intake
- Verdict-oriented city assessment
- Evidence panel with confidence and provenance labels
- Next-action guidance
- Chicago baseline comparison for David mode
- Transparent decision logic
- Confidence and provenance labels
- Validation-backed city dataset

Not included in MVP claims:

- Generic “best city” rankings
- Map-first discovery as the primary home
- Radar-first comparison as the primary decision surface
- Watchlist persistence
- OAuth
- AWS production deployment polish
- Live Reddit harvesting
- Prediction-style claims

## MVP flow

Every MVP experience follows this order:

1. Situation: capture the offer, baseline city, candidate city, hard constraints, and soft preferences.
2. Verdict: return `Take the job`, `Viable but risky`, or `Keep looking`.
3. Evidence: show the facts, confidence labels, freshness, exclusions, and skeptic notes behind the verdict.
4. Next Action: tell the user what to verify, negotiate, research, or reject next.

## MVP decision policy

The decision engine is the source of truth. UI surfaces may summarize it, but must not invent alternate ranking or verdict logic.

Hard constraints dominate scores. A city that fails a hard constraint cannot be rescued by a high aggregate score or strong soft-preference match.

Decision evidence may include only clearly labeled:

- Affordability
- Job market
- Safety
- Climate
- Civic-fit proxy
- Downtown-vibe proxy

Social sentiment is visible as context only and must not decide a verdict. Hardcoded civic leaning is not real evidence; civic fit must be sourced or explicitly labeled as missing/proxy/seeded.

## MVP trust policy

- A city is eligible for a confident verdict only when required hard-constraint evidence is source-backed and fresh enough for the decision.
- Estimated or imputed core dimensions may still appear in detail view, but the city is inspection-only and excluded from ranked discovery.
- Seeded Reddit context may appear in the product, but it must be labeled `seeded` and excluded from ranking.
- Seeded, proxy, stale, and missing evidence must be visible anywhere it affects interpretation.
- When evidence is insufficient, the verdict must say so instead of filling the gap with a score.

## MVP removal and de-emphasis

Remove or de-emphasize:

- Map-first home screen
- Generic ranking claims
- Social Buzz as decisive evidence
- Hardcoded civic leaning as real evidence
- Radar-first comparison

## Success criteria

- David can evaluate a specific offer against Chicago and see a clear verdict, evidence, and next action.
- Sarah's skeptic checks are visible in the product whenever evidence is weak, stale, proxy-only, seeded, or missing.
- Users can tell what the decision includes and excludes without reading code.
- Verdicts are based only on eligible, labeled evidence and hard constraints.
- Every dataset build produces a validation report summarizing coverage and eligibility.
- The UI reflects data confidence clearly enough that a reasonable user would not mistake seeded context for ranked evidence.
