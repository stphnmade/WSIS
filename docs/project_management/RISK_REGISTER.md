# WSIS Risk Register

| Risk | Severity | Status | Mitigation |
| --- | --- | --- | --- |
| Product is too broad and competes with mature city-ranking sites. | High | Open | Reposition WSIS as decision triage for a specific move. |
| Dataset is too small for trustworthy rankings. | High | Open | Show dataset coverage, limit claims, and prioritize hard-constraint verdicts. |
| Proxy fields are mistaken for strong evidence. | High | Open | Sarah review must label proxies, seeded fields, stale dates, and missing data. |
| Civic fit is hardcoded too broadly. | High | Open | Replace state-level placeholders with county/metro civic-fit sources. |
| Reddit context is seeded but visually persuasive. | Medium | Open | Keep social context out of verdict scoring and label it clearly. |
| UI repeats explanations and overwhelms users. | Medium | Open | Use verdict-first UI and progressive evidence disclosure. |
| Mobile layout regresses after map changes. | Medium | Open | Add responsive QA checklist and screenshot verification. |
| Deployment plan is aspirational. | Medium | Open | Define actual AWS services, env vars, secrets, and cost guardrails. |

## Sarah Quality Gate

Every recommendation must be able to survive these questions:

- What hard constraints passed or failed?
- What data is source-backed?
- What data is estimated, seeded, stale, or missing?
- What claim is WSIS not allowed to make?
- Would a competitor already answer this better?
