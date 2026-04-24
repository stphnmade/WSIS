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

## Hard constraints

- The app must make rent feasibility explicit
- If no city matches the rent target, the app must say so directly
- Chicago must always be present as the baseline comparison city in David mode

## Soft preferences

- warmer weather
- stronger downtown vibe
- independent civic-fit proxy
- positive contextual reviews

## Current product gap

The current dataset does not contain a single city with `median_rent < $980`, so the app cannot yet satisfy David's brief honestly. The next MVP pass must therefore:

- expand the city set
- add independent civic-fit data
- add downtown-vibe proxy data
- add offer-based salary-fit logic
- provide a verdict-oriented comparison against Chicago
