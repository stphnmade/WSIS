# David API And Data Plan

This plan defines the missing APIs and datasets needed for WSIS to serve User 0 (David) honestly as a relocation decision triage product.

David's decision:

- home city: Chicago
- offer: `$70,000`
- wants a city that feels civically compatible by independent proxy
- wants warmer weather than Chicago
- wants strong downtown energy
- wants affordability with average rent below `$980`

## Current blockers

- the current sample dataset has no city with average rent below `$980`
- there is no salary-offer fit calculation
- there is no independent civic-fit proxy
- there is no downtown-vibe proxy
- there is no decision verdict comparing a candidate city against Chicago
- seeded, proxy, stale, and missing evidence are not yet consistently visible in the decision surface

## Decision API target

The MVP API should return one decision object shaped around:

- Situation: offer, baseline city, candidate city, hard constraints, and soft preferences
- Verdict: `Take the job`, `Viable but risky`, or `Keep looking`
- Evidence: sourced values, confidence labels, freshness, and Sarah-style skeptic notes
- Next Action: specific follow-up such as verify rent, negotiate salary, inspect commute, or reject the city

The decision engine is the source of truth. UI components may summarize it, but must not recalculate or override verdicts.

## Must-have integrations

### 1. Rent and income

Purpose:
- determine whether David's hard rent target is even achievable
- compare candidate city rent burden against Chicago

Recommended source:
- U.S. Census ACS via API

Why:
- official source
- broad city/county coverage
- stable rent and income fields

Reference:
- [ACS data via API](https://www.census.gov/programs-surveys/acs/data/data-via-api.html)
- [Census API handbook](https://www.census.gov/programs-surveys/acs/library/handbooks/api.html)

Needed output:
- median rent
- median income
- population
- city/county mapping

### 2. Job market and wage context

Purpose:
- test whether a `$70,000` offer is competitive or weak in a city
- compare labor-market quality against Chicago

Recommended sources:
- BLS Public Data API
- BLS OEWS wage data
- BLS LAUS unemployment data

Why:
- official source
- no partisan framing
- lets us compare offer salary against local wage benchmarks and unemployment

Reference:
- [BLS Data API](https://www.bls.gov/bls/api_features.htm)
- [BLS developer getting started](https://www.bls.gov/developers/home.htm)

Needed output:
- unemployment rate
- occupation wage benchmark where feasible
- metro or county wage context

### 3. Climate and warmth

Purpose:
- compare candidate city warmth against Chicago
- expose typical climate rather than anecdotal weather

Recommended source:
- NOAA climate normals

Reference:
- [U.S. Climate Normals](https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals)

Needed output:
- average temperature
- seasonal comfort proxy
- sunny days or equivalent

### 4. Civic-fit proxy

Purpose:
- provide an independent non-media proxy for David's civic or political compatibility preference

Recommended source:
- MIT Election Lab county presidential returns, with official state election data as spot checks if needed

Reference:
- [MIT Election Lab data](https://electionlab.mit.edu/data)

Needed output:
- county- or metro-level Democratic/Republican vote share
- normalized civic-fit proxy

Important rule:
- this should be framed as a civic-fit proxy, not a moral or news-based label

### 5. Downtown-vibe proxy

Purpose:
- estimate whether a city has the downtown energy David wants

Recommended source:
- OpenStreetMap / Overpass-based amenity and transit density

Why:
- independent
- open
- measurable

Needed output:
- amenity density in core area
- restaurant/bar/cafe density
- walk/transit proxy
- central business district activity proxy

## Context-only integrations

### 6. Social / review context

Purpose:
- support qualitative city texture
- provide user-readable context on downtown feel, friendliness, nightlife, and newcomer experience

Current status:
- keep existing seeded Reddit summaries as context-only

Later additions:
- more review-like public context sources, if license and API terms allow

Important rule:
- context sources must not silently become rank-defining

## Product logic we still need

### Salary-fit engine

Needed calculations:
- rent as percent of offered salary
- rent as percent of estimated take-home pay
- offer benchmark versus local wages
- Chicago delta

### Hard-constraint engine

Needed checks:
- `median_rent < 980`
- warmer than Chicago
- civic-fit threshold
- downtown-vibe minimum

Rules:
- hard constraints dominate aggregate scores
- failed hard constraints must be visible in the verdict
- insufficient evidence must produce a lower-confidence verdict or next action, not a hidden pass

### Verdict layer

Needed outputs:
- `Take the job`
- `Viable but risky`
- `Keep looking`

The app must also say:
- when no city satisfies David's rent target
- when a city is warmer but still unaffordable
- when a city beats Chicago on some soft preferences but fails the core budget test
- when civic fit is hardcoded, proxy-only, stale, missing, or otherwise not real evidence

### Sarah quality gate

Every verdict should include skeptic checks:
- what evidence is source-backed
- what evidence is seeded or proxy-only
- what evidence is stale or missing
- what assumption would most likely change the verdict
- whether Social Buzz is being treated only as context

## Priority order

1. Census ACS rent/income
2. BLS unemployment and wage context
3. NOAA climate normals
4. MIT Election Lab civic-fit proxy
5. OpenStreetMap downtown-vibe proxy
6. stronger context/review sources
