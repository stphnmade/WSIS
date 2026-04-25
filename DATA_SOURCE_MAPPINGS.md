# Field-Level Source Mappings

## Identity and geography

- `city_slug`, `city_name`, `state_code`, `state_name`, `county_fips`, `county_name`, `latitude`, `longitude`, `population`
  source: `data/raw/simplemaps/us_cities.csv`
  caveat: SimpleMaps remains the city anchor and fallback geography file; ACS may override `population` when present.

## Core Public Reliable Feed v1

## Ranked MVP dimensions

- `affordability_*`
  source: `data/raw/census/acs_city_metrics.csv`
  public source target: Census ACS 5-Year profile/table extracts normalized to city rows
  current ranked input: median rent, median income, and HUD FMR practical rent context
  added fields: `education_bachelors_pct`, `mean_commute_minutes`
  join: `city_state_key` plus `county_fips`
  caveat: current file is a local normalized seed in the ACS target shape; external API/download failures should preserve this file and mark missing rows as estimated.

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
- these proxy fields remain visible, but they are not what makes a city eligible for ranked MVP discovery
- no live external downloader is part of this milestone; local normalized seed files keep the app runnable if public-feed refreshes fail
- no OAuth, AWS deployment, live Reddit, or choropleth work is included in this data milestone
