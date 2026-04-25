# User 0: David

## Profile

- Early-career user
- Home city: Chicago
- Offer under evaluation: `$70,000`
- Wants a city that feels liberal by independent civic proxy, not by partisan media framing
- Wants warmer weather than Chicago
- Wants strong downtown energy and useful public reviews/context
- Wants affordability and an average rent below `$980`

## Decision job

David is not browsing casually. He is deciding whether to:

1. take a specific job in another city
2. stay in Chicago
3. keep looking

David is the canonical MVP user. WSIS should optimize for his relocation triage decision before adding generic discovery or ranking features.

## Sarah quality gate

Sarah is the built-in skeptic for David's decision. She asks:

- Is the rent target actually satisfied?
- Is the offer strong enough for this market?
- Is the civic-fit evidence sourced, or only hardcoded/proxy?
- Is social context being treated as texture rather than proof?
- What evidence is stale, missing, seeded, or too weak for a confident verdict?

If Sarah would not trust the evidence, the product must lower confidence and give a next action instead of forcing a positive verdict.

## MVP flow

1. Situation: David enters the offer, current city, candidate city, hard constraints, and soft preferences.
2. Verdict: WSIS returns `Take the job`, `Viable but risky`, or `Keep looking`.
3. Evidence: WSIS shows rent, salary fit, climate, jobs, safety, civic-fit proxy, downtown-vibe proxy, and context labels.
4. Next Action: WSIS tells David what to verify, negotiate, research, or reject.

## Hard constraints

- The app must make rent feasibility explicit
- If no city matches the rent target, the app must say so directly
- Chicago must always be present as the baseline comparison city in David mode
- Hard constraints dominate any aggregate score or soft-preference match

## Soft preferences

- warmer weather
- stronger downtown vibe
- independent civic-fit proxy
- positive contextual reviews

Soft preferences can explain a verdict but cannot override a failed hard constraint.

## Current product gap

The current dataset does not contain a single city with `median_rent < $980`, so the app cannot yet satisfy David's brief honestly. The next MVP pass must therefore:

- expand the city set
- add independent civic-fit data
- add downtown-vibe proxy data
- add offer-based salary-fit logic
- provide a verdict-oriented comparison against Chicago

## Must remove or de-emphasize for David mode

- Map-first home
- Generic city ranking claims
- Social Buzz as decisive evidence
- Hardcoded civic leaning presented as real evidence
- Radar-first comparison as the primary decision surface
