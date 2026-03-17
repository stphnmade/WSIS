from __future__ import annotations

from pydantic import BaseModel, Field

from wsis.domain.models import CityMetrics


class CityProfileRecord(BaseModel):
    city_slug: str
    city_name: str
    city_name_normalized: str
    city_state_key: str
    state_code: str
    state_name: str
    county_fips: str = Field(min_length=5, max_length=5)
    county_name: str
    region: str
    latitude: float
    longitude: float
    population: int
    median_income: float
    median_rent: float
    median_home_price: float
    unemployment_pct: float
    job_growth_pct: float
    violent_crime_per_100k: float
    safety_score_raw: float = Field(ge=0, le=100)
    avg_temp_f: float
    sunny_days: float
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
    headline: str
    known_for: str

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
            safety_score_raw=self.safety_score_raw,
            climate_score_raw=self.climate_score_raw,
            social_sentiment_raw=self.social_sentiment_raw,
            known_for=self.known_for,
        )

