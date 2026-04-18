from __future__ import annotations

from pydantic import BaseModel, Field

from wsis.domain.models import CityMetrics


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
    "unemployment_pct",
    "job_growth_pct",
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
    "has_simplemaps_data",
    "has_census_data",
    "has_bls_data",
    "has_fbi_data",
    "has_noaa_data",
    "has_reddit_data",
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
    unemployment_pct: float = Field(ge=0, le=100)
    job_growth_pct: float = Field(ge=-100, le=100)
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
    has_simplemaps_data: bool
    has_census_data: bool
    has_bls_data: bool
    has_fbi_data: bool
    has_noaa_data: bool
    has_reddit_data: bool
    headline: str = Field(min_length=1)
    known_for: str = Field(min_length=1)

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
            median_income=self.median_income,
            job_growth_pct=self.job_growth_pct,
            unemployment_pct=self.unemployment_pct,
            violent_crime_per_100k=self.violent_crime_per_100k,
            safety_score_raw=self.safety_score_raw,
            avg_temp_f=self.avg_temp_f,
            sunny_days=self.sunny_days,
            climate_score_raw=self.climate_score_raw,
            social_sentiment_raw=self.social_sentiment_raw,
            known_for=self.known_for,
        )
