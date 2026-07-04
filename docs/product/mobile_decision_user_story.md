# Mobile Decision User Story

## Story

As David, a recent graduate evaluating an out-of-state job offer, I want to use
WSIS comfortably from my phone so that I can determine whether the move fits my
budget, career needs, and risk tolerance before I accept the offer.

## Primary scenario

David opens the deployed WSIS URL on a 390×844 phone over a normal mobile
connection. He enters:

- current city: Chicago, IL
- offer city: Austin, TX
- annual salary: $72,000
- maximum monthly rent: $1,800
- priorities: affordability and job market first

WSIS returns a clear verdict, explains any hard-constraint failures, shows the
freshness and confidence of the supporting data, and provides a concrete next
action. David can inspect Austin's current new-graduate job listings and compare
Austin with Chicago without using a desktop-only table or precise map taps.

## Acceptance criteria

### Responsive behavior

- The complete journey works at 360×740, 390×844, and 430×932.
- No page has horizontal scrolling or clipped controls.
- Interactive targets are at least 44×44 px.
- The primary action is reachable in the first viewport.
- The map is optional; city selection and comparison work through accessible lists.

### Decision behavior

- Required fields have visible labels and inline validation.
- The submitted situation is evaluated by the FastAPI decision endpoint.
- Hard constraints appear before aggregate scores.
- The verdict is one of `Take the job`, `Viable but risky`, or `Keep looking`.
- Evidence includes affordability, job market, safety, climate, confidence, and source date.
- Social sentiment is labeled as context-only and cannot change the verdict.
- A specific next action is displayed.

### Loading and failure behavior

- The application shell renders immediately without a page-blocking spinner.
- Geometry-matched skeletons appear while verdict and profile data load.
- Repeated profile visits use cached data and refresh in the background.
- A failed API request preserves David's form values and exposes a retry action.
- An offline revisit shows cached profiles in a clearly labeled read-only state.

### Job information

- Austin displays matching active new-graduate roles from the normalized GitHub feed.
- Each role shows company, title, location, posting/update date, and external URL.
- Empty results are presented as an empty state, not as zero market demand.

### Free-service deployment

- Frontend and API origins are configured through environment variables.
- The health endpoint returns HTTP 200 from the public deployment.
- The public frontend can call the API without CORS or mixed-content errors.
- Cold-start behavior shows a useful loading state and recovers without re-entry.
- Deployment does not depend on a writable local filesystem for persistent state.
- Scheduled data refresh runs separately through GitHub Actions and commits validated artifacts.

## Manual test script

1. Open the production URL in a private mobile browser session at 390×844.
2. Enable a throttled mobile network profile.
3. Complete the primary scenario and submit it once.
4. Confirm the verdict, hard constraints, evidence freshness, and next action.
5. Open Austin's profile and one external job listing.
6. Compare Austin with Chicago using the non-map interface.
7. Navigate back and confirm the situation remains populated.
8. Simulate an API failure, retry, and confirm no form data is lost.
9. Reopen a previously visited profile while offline and verify the read-only state.
10. Run the same critical journey at 360×740 and at desktop width.

## Automated test cases

- `mobile decision happy path`
- `hard constraint overrides aggregate score`
- `slow API renders skeleton then verdict`
- `API failure preserves form and retries`
- `discovery succeeds when map bundle is blocked`
- `job listing opens with source metadata`
- `Chicago and one candidate stack on mobile`
- `deep-linked profile works after a cold server start`
- `no horizontal overflow at supported widths`

## Definition of done

- All acceptance criteria pass against the public deployment.
- Playwright covers the automated cases at 390×844 and desktop width.
- Lighthouse mobile scores at least 90 for performance and 95 for accessibility.
- FastAPI, frontend, and scheduled data refresh each expose actionable failure logs.
