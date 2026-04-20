from __future__ import annotations

from pydantic import BaseModel, Field

from wsis.domain.models import CityMetrics, DimensionTrust


CITY_PROFILE_REQUIRED_COLUMNS = (
    "city_slug",
    "city_name",
    "city_name_normalized",
    "city_state_key",
    "state_code",
    "state_name",
    "county_fips",
    "county_name",
    "region",
    "latitude",
    "longitude",
    "population",
    "median_income",
    "median_rent",
    "median_home_price",
    "median_home_price_source",
    "median_home_price_source_date",
    "median_home_price_is_imputed",
    "unemployment_pct",
    "job_growth_pct",
    "job_growth_source",
    "job_growth_source_date",
    "job_growth_is_imputed",
    "violent_crime_per_100k",
    "safety_score_raw",
    "avg_temp_f",
    "sunny_days",
    "climate_score_raw",
    "social_sentiment_raw",
    "affordability_norm",
    "job_market_norm",
    "safety_norm",
    "climate_norm",
    "social_norm",
    "affordability_confidence",
    "affordability_source",
    "affordability_source_date",
    "affordability_is_imputed",
    "job_market_confidence",
    "job_market_source",
    "job_market_source_date",
    "job_market_is_imputed",
    "safety_confidence",
    "safety_source",
    "safety_source_date",
    "safety_is_imputed",
    "climate_confidence",
    "climate_source",
    "climate_source_date",
    "climate_is_imputed",
    "social_confidence",
    "social_source",
    "social_source_date",
    "social_is_imputed",
    "is_mvp_eligible",
    "has_simplemaps_data",
    "has_census_data",
    "has_bls_data",
    "has_fbi_data",
    "has_noaa_data",
    "has_reddit_data",
    "has_cost_of_living_context",
    "has_jobs_context",
    "headline",
    "known_for",
)

CITY_PROFILE_UNIQUE_COLUMNS = ("city_slug", "city_state_key")

CITY_PROFILE_RANGE_RULES = {
    "latitude": (-90, 90),
    "longitude": (-180, 180),
    "population": (1, 10_000_000_000),
    "median_income": (1, 10_000_000),
    "median_rent": (1, 100_000),
    "median_home_price": (1, 100_000_000),
    "unemployment_pct": (0, 100),
    "job_growth_pct": (-100, 100),
    "violent_crime_per_100k": (0, 100_000),
    "safety_score_raw": (0, 100),
    "avg_temp_f": (-50, 150),
    "sunny_days": (0, 366),
    "climate_score_raw": (0, 100),
    "social_sentiment_raw": (-1, 1),
    "affordability_norm": (0, 1),
    "job_market_norm": (0, 1),
    "safety_norm": (0, 1),
    "climate_norm": (0, 1),
    "social_norm": (0, 1),
}

CITY_PROFILE_NON_EMPTY_STRING_COLUMNS = (
    "city_slug",
    "city_name",
    "city_name_normalized",
    "city_state_key",
    "state_code",
    "state_name",
    "county_fips",
    "county_name",
    "region",
    "headline",
    "known_for",
    "affordability_confidence",
    "affordability_source",
    "affordability_source_date",
    "job_market_confidence",
    "job_market_source",
    "job_market_source_date",
    "median_home_price_source",
    "median_home_price_source_date",
    "job_growth_source",
    "job_growth_source_date",
    "safety_confidence",
    "safety_source",
    "safety_source_date",
    "climate_confidence",
    "climate_source",
    "climate_source_date",
    "social_confidence",
    "social_source",
    "social_source_date",
)


class CityProfileRecord(BaseModel):
    city_slug: str = Field(min_length=1)
    city_name: str = Field(min_length=1)
    city_name_normalized: str = Field(min_length=1)
    city_state_key: str = Field(min_length=1)
    state_code: str = Field(min_length=2, max_length=2)
    state_name: str = Field(min_length=1)
    county_fips: str = Field(min_length=5, max_length=5)
    county_name: str = Field(min_length=1)
    region: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    population: int = Field(gt=0)
    median_income: float = Field(gt=0)
    median_rent: float = Field(gt=0)
    median_home_price: float = Field(gt=0)
    median_home_price_source: str = Field(min_length=1)
    median_home_price_source_date: str = Field(min_length=1)
    median_home_price_is_imputed: bool
    unemployment_pct: float = Field(ge=0, le=100)
    job_growth_pct: float = Field(ge=-100, le=100)
    job_growth_source: str = Field(min_length=1)
    job_growth_source_date: str = Field(min_length=1)
    job_growth_is_imputed: bool
    violent_crime_per_100k: float = Field(ge=0)
    safety_score_raw: float = Field(ge=0, le=100)
    avg_temp_f: float = Field(ge=-50, le=150)
    sunny_days: float = Field(ge=0, le=366)
    climate_score_raw: float = Field(ge=0, le=100)
    social_sentiment_raw: float = Field(ge=-1, le=1)
    affordability_norm: float = Field(ge=0, le=1)
    job_market_norm: float = Field(ge=0, le=1)
    safety_norm: float = Field(ge=0, le=1)
    climate_norm: float = Field(ge=0, le=1)
    social_norm: float = Field(ge=0, le=1)
    affordability_confidence: str = Field(min_length=1)
    affordability_source: str = Field(min_length=1)
    affordability_source_date: str = Field(min_length=1)
    affordability_is_imputed: bool
    job_market_confidence: str = Field(min_length=1)
    job_market_source: str = Field(min_length=1)
    job_market_source_date: str = Field(min_length=1)
    job_market_is_imputed: bool
    safety_confidence: str = Field(min_length=1)
    safety_source: str = Field(min_length=1)
    safety_source_date: str = Field(min_length=1)
    safety_is_imputed: bool
    climate_confidence: str = Field(min_length=1)
    climate_source: str = Field(min_length=1)
    climate_source_date: str = Field(min_length=1)
    climate_is_imputed: bool
    social_confidence: str = Field(min_length=1)
    social_source: str = Field(min_length=1)
    social_source_date: str = Field(min_length=1)
    social_is_imputed: bool
    is_mvp_eligible: bool
    has_simplemaps_data: bool
    has_census_data: bool
    has_bls_data: bool
    has_fbi_data: bool
    has_noaa_data: bool
    has_reddit_data: bool
    has_cost_of_living_context: bool
    has_jobs_context: bool
    headline: str = Field(min_length=1)
    known_for: str = Field(min_length=1)

    def _dimension_trust(self, dimension: str) -> DimensionTrust:
        confidence = getattr(self, f"{dimension}_confidence")
        source = getattr(self, f"{dimension}_source")
        source_date = getattr(self, f"{dimension}_source_date")
        is_imputed = getattr(self, f"{dimension}_is_imputed")
        note_map = {
            "affordability": "Built from rent burden against local median income; median home price stays visible as separate context.",
            "job_market": "Built from source-backed unemployment data; job-growth context stays visible separately and does not change the MVP rank.",
            "safety": "Derived from the current crime-rate slice anchored to the city's county FIPS.",
            "climate": "Derived from the current climate slice anchored to the city's county FIPS.",
            "social": "Social sentiment is visible as context only and does not change the MVP rank.",
        }
        return DimensionTrust(
            confidence=confidence,
            source=source,
            source_date=source_date,
            is_imputed=is_imputed,
            note=note_map[dimension],
        )

    def to_city_metrics(self) -> CityMetrics:
        return CityMetrics(
            slug=self.city_slug,
            name=self.city_name,
            state=self.state_name,
            state_code=self.state_code,
            region=self.region,
            headline=self.headline,
            population=self.population,
            latitude=self.latitude,
            longitude=self.longitude,
            median_rent=self.median_rent,
            median_home_price=self.median_home_price,
            median_home_price_source=self.median_home_price_source,
            median_home_price_source_date=self.median_home_price_source_date,
            median_home_price_is_imputed=self.median_home_price_is_imputed,
            median_income=self.median_income,
            job_growth_pct=self.job_growth_pct,
            job_growth_source=self.job_growth_source,
            job_growth_source_date=self.job_growth_source_date,
            job_growth_is_imputed=self.job_growth_is_imputed,
            unemployment_pct=self.unemployment_pct,
            violent_crime_per_100k=self.violent_crime_per_100k,
            safety_score_raw=self.safety_score_raw,
            avg_temp_f=self.avg_temp_f,
            sunny_days=self.sunny_days,
            climate_score_raw=self.climate_score_raw,
            social_sentiment_raw=self.social_sentiment_raw,
            affordability_trust=self._dimension_trust("affordability"),
            job_market_trust=self._dimension_trust("job_market"),
            safety_trust=self._dimension_trust("safety"),
            climate_trust=self._dimension_trust("climate"),
            social_trust=self._dimension_trust("social"),
            is_mvp_eligible=self.is_mvp_eligible,
            known_for=self.known_for,
        )
