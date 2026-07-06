# WSIS Roadmap

## Product Direction

WSIS is moving from broad city ranking toward relocation decision triage.

The product should answer whether a move is viable for a specific user, offer, baseline city, rent target, and preference set. Generic livability rankings are secondary.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M1: Decision-first product frame | Replace broad ranking language with a verdict-oriented product model. | In progress |
| M2: David decision flow | Evaluate offer salary, rent target, Chicago baseline, warmth, civic fit, and downtown energy. | Planned |
| M3: Sarah skeptic review | Flag weak data, seeded context, proxies, stale sources, and unsupported claims. | Planned |
| M4: Data reliability pass | Replace proxy fields where possible and add provider/key tracking. | Planned |
| M5: UI simplification | Reduce duplicate text, keep one primary action per screen, and use progressive evidence disclosure. | Planned |
| M6: Mobile QA | Verify iPhone-size layouts, cards, touch targets, and no overlapping/duplicated information. | Planned |
| M7: Deployment readiness | Lock env vars, secret handling, CI checks, and AWS free-tier deployment plan. | Planned |

## Near-Term Work

1. Finish map/homepage interaction cleanup and responsive validation.
2. Add David and Sarah acceptance tests.
3. Build decision verdict data contract.
4. Create ClickUp milestone tasks and keep them synchronized with GitHub commits and PRs.
5. Create Google Drive status/reporting assets only when shared review artifacts are needed.

## Success Criteria

- David can get a decision verdict in under 60 seconds.
- Sarah can audit every verdict for weak evidence.
- WSIS clearly distinguishes source-backed, estimated, seeded, stale, and missing data.
- The UI avoids redundant explanations and exposes detail only when useful.
- Every milestone has ClickUp status, owner, risk, and next action.
