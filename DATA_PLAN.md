# Data Plan

Sources

GitHub city/state geography (`dr5hn/countries-states-cities-database`)
US Census ACS (credentialed API refresh)
BLS Local Area Unemployment Statistics (API refresh)
GitHub new-grad listings (`SimplifyJobs/New-Grad-Positions`)
MIT Living Wage
FBI Crime
Zillow Housing
NOAA Climate
EPA Environment
Reddit API

Primary join key: county FIPS

Run current live feeds with `python3 -m wsis.data.refresh`. The scheduled
`.github/workflows/data-refresh.yml` workflow refreshes, validates, and commits data daily.
