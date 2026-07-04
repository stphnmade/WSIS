# Field-Level Source Mappings

## Identity and geography

- `city_slug`, `city_name`, `state_code`, `state_name`, `county_fips`, `county_name`, `latitude`, `longitude`, `population`
  primary normalized source: `data/raw/github/us_cities.csv`, refreshed through the GitHub Contents API from `dr5hn/countries-states-cities-database`
  fallback: `data/raw/simplemaps/us_cities.csv`
  caveat: GitHub refreshes city/state identity, coordinates, population, and timezone. County name/FIPS remain pinned to the canonical crosswalk because the GitHub source does not contain county FIPS; ACS may override `population` when present.

## Core Public Reliable Feed v1

## Ranked MVP dimensions

- `affordability_*`
  source: `data/raw/census/acs_city_metrics.csv`
  public source target: Census ACS 5-Year profile/table extracts normalized to city rows
  current ranked input: median rent, median income, and HUD FMR practical rent context
  added fields: `education_bachelors_pct`, `mean_commute_minutes`
  join: `city_state_key` plus `county_fips`
  refresh: `python3 -m wsis.data.refresh --source census` with `CENSUS_API_KEY`
  caveat: the current file remains the last-known-good normalized input when a refresh is unavailable.

- `fair_market_rent_*`, `rent_to_fmr_ratio`, `practical_rent_gap`
  source: `data/raw/hud/fair_market_rents.csv`
  public source target: HUD Fair Market Rents, 2-bedroom FMR by county/FMR area
  ranked role: practical affordability input inside `affordability_*`
  join: `county_fips`
  caveat: FMR area boundaries can span multiple counties; WSIS currently stores a county-level normalized slice.

- `population`
  source priority: ACS `population` from `data/raw/census/acs_city_metrics.csv`, falling back to SimpleMaps population
  note: derived home-price proxy remains visible as context but is not required for ranked eligibility

- `job_market_*`
  source: `data/raw/bls/county_unemployment.csv`
  public source target: BLS Local Area Unemployment Statistics
  current ranked input: unemployment rate
  join: `county_fips`
  note: proxy `job_growth_pct` remains visible as context and does not determine MVP eligibility

- `newgrad_job_*`, `newgrad_jobs_*`, `has_newgrad_jobs_context`
  primary source: GitHub Contents API for `SimplifyJobs/New-Grad-Positions/.github/scripts/listings.json`
  normalized file: `data/raw/github/newgrad_jobs.csv`
  listing-level file: `data/raw/github/newgrad_job_listings.csv` (company, title, URL, category, location, posting dates, and sponsorship signal)
  fallback source: `https://www.newgrad-jobs.com/entry-level-jobs` and its sitemap
  local fallback: `data/source_samples/newgrad_jobs.csv`
  role: supplemental early-career job-market context only
  join: `city_slug` plus `county_fips`
  caveat: NewGrad Jobs is a public third-party listing/index page with city pages and Airtable embeds; WSIS treats it as a volatile market signal, not a ranked eligibility source. BLS LAUS remains the ranked job-market source.

- `safety_*`
  source: `data/raw/fbi/county_crime.csv`
  current ranked input: county crime slice mapped by `county_fips`

- `climate_*`
  source: `data/raw/noaa/county_climate.csv`
  public source target: NOAA Climate Normals
  current ranked input: average temperature and sunny-day proxy mapped by `county_fips`
  caveat: NOAA station normals do not naturally publish as county rows; WSIS expects a normalized county-level extract.

## Filter-ready booleans

- `is_warm`
  derived from average temperature or climate score
- `is_affordable`
  derived from rent burden or HUD FMR ratio
- `is_high_income`
  derived from median income
- `is_strong_job_market`
  derived from unemployment rate or normalized job-market score
- `has_newgrad_jobs_context`
  true when NewGrad Jobs scrape or local seed has a city-level early-career jobs signal

## Context-only social dimension

- `social_*`
  source: `data/raw/reddit/city_sentiment.csv`
  confidence: currently `seeded`
  ranking status: excluded from ranked MVP score

- detail-view social summaries
  source: `data/raw/reddit/city_sentiment_summaries.json`
  ranking status: excluded from ranked MVP score

## Current caveats

- `median_home_price` is still a rent-derived proxy
- `job_growth_pct` is still an unemployment-derived proxy
- NewGrad Jobs context is scrape-backed when reachable and seed-backed otherwise; it should not be used as a source-backed public labor statistic
- these proxy fields remain visible, but they are not what makes a city eligible for ranked MVP discovery
- live GitHub geography, GitHub job listings, BLS, and credentialed Census refreshers are implemented; last-known-good raw files keep the app runnable when a feed fails
- no OAuth, AWS deployment, live Reddit, or choropleth work is included in this data milestone
