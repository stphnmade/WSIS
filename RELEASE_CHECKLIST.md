# WSIS MVP Readiness Checklist

Definition of success for an MVP release:

- The Decision page answers "Should I seriously consider this move?" before any broad ranking language.
- Every page renders without raw HTML/code blocks.
- Desktop and mobile layouts avoid horizontal overflow and clipped labels.
- `city_profiles.parquet` is rebuilt from the pipeline and validated before release.
- Source freshness and source coverage are visible in `data/processed/city_profiles_validation_report.json`.
- ACS, BLS, HUD, and NOAA remain the source-backed core. NewGrad Jobs remains context-only.
- Social sentiment and NewGrad Jobs are clearly treated as supplemental context.

Release commands:

```bash
python scripts/wsis_readiness_check.py
```

With the Streamlit app running:

```bash
WSIS_PLAYWRIGHT_PACKAGE=playwright node scripts/browser_smoke.mjs
```

If Playwright is only available through a local cache, point `WSIS_PLAYWRIGHT_PACKAGE` at that package path.
