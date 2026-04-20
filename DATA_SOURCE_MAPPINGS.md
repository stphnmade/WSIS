# Field-Level Source Mappings

## Identity and geography

- `city_slug`, `city_name`, `state_code`, `state_name`, `county_fips`, `county_name`, `latitude`, `longitude`, `population`
  source: `data/raw/simplemaps/us_cities.csv`

## Ranked MVP dimensions

- `affordability_*`
  source: `data/raw/census/acs_city_metrics.csv`
  current ranked input: median rent and median income
  note: derived home-price proxy remains visible as context but is not required for ranked eligibility

- `job_market_*`
  source: `data/raw/bls/county_unemployment.csv`
  current ranked input: unemployment rate
  note: proxy `job_growth_pct` remains visible as context and does not determine MVP eligibility

- `safety_*`
  source: `data/raw/fbi/county_crime.csv`
  current ranked input: county crime slice mapped by `county_fips`

- `climate_*`
  source: `data/raw/noaa/county_climate.csv`
  current ranked input: county climate slice mapped by `county_fips`

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
