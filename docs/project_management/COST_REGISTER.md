# WSIS Cost Register

## Cost Policy

Use free-tier and no-key public datasets first. Ask before adding any paid API, recurring cloud service, or paid data license.

## Current Cost Baseline

| Category | Provider | Status | Expected Cost | Notes |
| --- | --- | --- | ---: | --- |
| Census data | U.S. Census API | Planned/free | $0 | API key recommended for higher limits. |
| Labor data | BLS Public Data API | Planned/free | $0 | Registered key improves access limits. |
| Climate data | NOAA CDO | Planned/free | $0 | Requires free token. |
| Crime data | FBI Crime Data API / api.data.gov | Planned/free | $0 | Requires free data.gov key. |
| Rent fallback | HUD USER FMR | Planned/free | $0 | Use before paid rent-estimate providers. |
| Social context | Reddit API | Optional/free with restrictions | $0 | Keep context-only unless data quality improves. |
| Amenities/downtown proxy | OpenStreetMap Overpass | Planned/free | $0 | Respect public instance limits. |
| Deployment | AWS Free Tier | Planned | $0 initially | Billing alarms required before deployment. |
| CI/CD | GitHub Actions | Existing/free | $0 | Public repo free tier expected. |

## Cost Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| AWS usage exceeds free tier | Unexpected bill | Add budget alarm, minimal services, and teardown notes. |
| Paid rent data becomes necessary | Monthly API cost | Use Census/HUD first; document missing precision. |
| Reddit policy or limits block sentiment work | Feature gap | Keep social context non-ranking and optional. |
| High-volume Overpass usage gets throttled | Data build failures | Cache extracts and avoid request-heavy live UI calls. |

## Approval Rule

No paid service may be added without an explicit user decision recorded in ClickUp or project documentation.
