# WSIS Responsive Web Plan

## Outcome

Build a mobile-first relocation decision website that feels immediate on a
390×844 phone, remains useful on slow networks, and preserves WSIS's trust-first
decision model.

The production frontend should be a React + TypeScript + Vite application that
uses the existing FastAPI service. Streamlit remains available as an internal
prototype and data-inspection tool during migration.

## Product flow

The primary phone journey is:

1. Situation — enter current city, offer city, salary, rent ceiling, and priorities.
2. Verdict — show the recommendation and hard-constraint failures immediately.
3. Evidence — show affordability, jobs, safety, climate, and source confidence.
4. Next action — provide specific verification, negotiation, or rejection steps.

Discovery and comparison remain available, but map interaction is supporting
context rather than the required mobile entry point.

## Architecture

```text
Browser / installable PWA
  React + TypeScript + Vite
  React Router
  TanStack Query cache
          |
          | JSON over HTTPS
          v
Existing FastAPI API
          |
          v
Scoring, decision services, and processed city data
```

Rules:

- Do not copy scoring or data-normalization logic into React.
- FastAPI remains the decision source of truth.
- Add frontend-specific API response shapes only through typed contracts.
- Use environment variables for API origin and observability configuration.
- Generate TypeScript API types from FastAPI's OpenAPI schema in CI.

## Responsive experience

### Mobile, 360–599 px

- Single-column layout with 16 px gutters.
- Bottom navigation for Decide, Discover, Compare, and Saved.
- Full-width primary actions and minimum 44×44 px touch targets.
- Verdict, salary/rent fit, and evidence freshness appear in the first viewport.
- Filters open in a bottom sheet; maps open as a secondary full-screen view.
- Comparison shows Chicago and one candidate as stacked sections.

### Tablet, 600–1023 px

- Two-column evidence layouts where content remains readable.
- Persistent filter rail only when it does not reduce the main content below 560 px.
- Map and city list can share the screen.

### Desktop, 1024 px and wider

- Maximum content width of approximately 1280 px.
- Decision input and verdict can sit side by side.
- Discovery uses a synchronized list and map without hiding the list fallback.

## Smart loading strategy

### Initial load

- Keep the application shell and first decision route in the initial bundle.
- Lazy-load map, charts, comparison, and city-detail routes.
- Load fonts with `font-display: swap`; avoid blocking third-party scripts.
- Serve responsive images in AVIF/WebP with explicit dimensions.
- Target less than 170 KB compressed JavaScript for the initial route.

### Data loading

- Use TanStack Query with stale-while-revalidate behavior.
- Cache the city index longer than individual profiles because it changes less often.
- Deduplicate requests and cancel superseded search/filter requests.
- Prefetch a city profile when its list row receives pointer, focus, or touch intent.
- Keep the previous comparison result visible while new data loads.
- Use URL state for shareable situation, filters, selected city, and comparison.

### Loading states

- Render the page shell immediately; never block the whole page with a spinner.
- Use skeletons that match the final verdict, metric row, and city-card geometry.
- Show partial evidence as each query resolves.
- Distinguish initial loading, background refresh, empty results, offline cache, and errors.
- Provide a retry action and preserve completed form input after failures.

### Resilience

- Cache the last successful city index and recently opened profiles in the browser.
- Show data timestamps and a non-blocking stale-data notice.
- Provide an offline read-only state for cached profiles.
- Add API timeouts, retry only idempotent reads, and use exponential backoff with jitter.

## Frontend structure

```text
apps/web/
  src/
    app/              # router, providers, error boundaries
    api/              # generated contracts and query functions
    components/       # reusable accessible UI primitives
    features/
      decision/
      discovery/
      city-profile/
      comparison/
      saved/
    styles/           # tokens, typography, responsive rules
    test/
```

Recommended baseline:

- React, TypeScript, Vite
- React Router
- TanStack Query
- React Hook Form with Zod validation
- Vitest and Testing Library
- Playwright for phone and desktop journeys
- MSW for deterministic loading, error, and slow-network tests

## Delivery phases

### Phase 0 — contracts and measurements

- Record current mobile screenshots and Lighthouse/Web Vitals baselines.
- Inventory FastAPI endpoints and identify missing decision/profile fields.
- Define generated TypeScript contracts and API error format.
- Establish phone test sizes: 360×740, 390×844, and 430×932.

Exit gate: OpenAPI generation succeeds and the critical journey has documented
request/response contracts.

### Phase 1 — visual system and application shell

- Produce and approve complete mobile concepts for Situation, Verdict, City Profile,
  Comparison, loading, empty, offline, and error states before implementation.
- Define tokens for color, typography, spacing, elevation, motion, and focus states.
- Build the responsive shell, navigation, route boundaries, and query provider.

Exit gate: shell works without horizontal scrolling at all target widths and is
keyboard navigable.

### Phase 2 — decision journey

- Implement situation form, validation, URL persistence, verdict, evidence, and next action.
- Add geometry-matched skeletons and resilient API error recovery.
- Make the hard-constraint result visible before aggregate scores.

Exit gate: a user can complete Situation → Verdict → Evidence → Next Action on a
390×844 viewport using keyboard or touch.

### Phase 3 — discovery and city profiles

- Implement mobile city list first, then lazy-load the map.
- Add filter bottom sheet, profile prefetch, provenance, job listings, and source freshness.
- Virtualize long result lists when city coverage expands.

Exit gate: discovery works with JavaScript map loading blocked and profiles expose
source confidence without layout shifts.

### Phase 4 — comparison, saved state, and PWA

- Implement stacked phone comparison and expanded desktop comparison.
- Add local saved cities and recent decisions without requiring an account.
- Add install manifest and offline read-only caching for recently viewed content.

Exit gate: Chicago plus one candidate can be compared on a phone without a wide table.

### Phase 5 — performance, accessibility, and rollout

- Run automated viewport, slow-network, offline, and API-failure scenarios.
- Audit WCAG 2.2 AA semantics, focus order, contrast, reduced motion, and screen readers.
- Deploy behind a feature flag, compare analytics and errors, then make React primary.
- Keep Streamlit available internally until production parity is confirmed.

Exit gate: all quality budgets pass in CI and production telemetry is stable.

## Quality budgets

Test on a mid-tier mobile profile with a throttled 4G connection:

- Largest Contentful Paint: ≤ 2.5 s at the 75th percentile.
- Interaction to Next Paint: ≤ 200 ms at the 75th percentile.
- Cumulative Layout Shift: ≤ 0.1.
- First route compressed JavaScript: ≤ 170 KB.
- No horizontal overflow at 360, 390, 430, 768, 1024, and 1440 px.
- Touch targets: at least 44×44 px.
- Lighthouse mobile: Performance ≥ 90, Accessibility ≥ 95.
- Critical API failure always exposes retry and preserves user input.

## Testing matrix

- Unit: formatters, query keys, validation, source-confidence presentation.
- Component: loading, success, empty, stale, offline, and error states.
- Contract: generated frontend types against FastAPI OpenAPI.
- End-to-end: decision, discovery without map, profile, comparison, deep links.
- Visual regression: target phone widths plus tablet and desktop.
- Performance: bundle budget and Lighthouse CI on every pull request.

## First implementation milestone

The first shippable slice is the mobile Decision route—not the homepage map:

1. Scaffold `apps/web` with React, TypeScript, and Vite.
2. Generate API types from FastAPI.
3. Implement the app shell and mobile navigation.
4. Implement Situation and Verdict against the real decision endpoint.
5. Add skeleton, slow-network, empty, and error states.
6. Verify at 390×844 and one desktop viewport with Playwright and visual screenshots.
