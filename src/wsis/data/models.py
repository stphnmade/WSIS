from __future__ import annotations

from pydantic import BaseModel, Field

from wsis.domain.models import CityMetrics


class SourceSliceMetadata(BaseModel):
    source_name: str
    source_vintage: int
    source_geography: str


class CityIndexRecord(BaseModel):
    city_slug: str
    name: str
    state: str
    state_code: str
    region: str
    county_fips: str = Field(min_length=5, max_length=5)
    county_name: str
    headline: str
    population: int
    latitude: float
    longitude: float
    known_for: str


class CostOfLivingRecord(SourceSliceMetadata):
    county_fips: str = Field(min_length=5, max_length=5)
    median_rent: float
    median_home_price: float
    median_income: float


class JobsRecord(SourceSliceMetadata):
    county_fips: str = Field(min_length=5, max_length=5)
    job_growth_pct: float
    unemployment_pct: float


class SafetyRecord(SourceSliceMetadata):
    county_fips: str = Field(min_length=5, max_length=5)
    safety_score_raw: float = Field(ge=0, le=100)


class ClimateRecord(SourceSliceMetadata):
    county_fips: str = Field(min_length=5, max_length=5)
    climate_score_raw: float = Field(ge=0, le=100)


class SocialSentimentRecord(SourceSliceMetadata):
    city_slug: str
    county_fips: str = Field(min_length=5, max_length=5)
    social_sentiment_raw: float = Field(ge=-1, le=1)


class CanonicalCityRecord(BaseModel):
    """MVP canonical record: one city anchored to one county FIPS join key."""

    city_slug: str
    county_fips: str = Field(min_length=5, max_length=5)
    county_name: str
    name: str
    state: str
    state_code: str
    region: str
    headline: str
    population: int
    latitude: float
    longitude: float
    known_for: str
    median_rent: float
    median_home_price: float
    median_income: float
    job_growth_pct: float
    unemployment_pct: float
    safety_score_raw: float = Field(ge=0, le=100)
    climate_score_raw: float = Field(ge=0, le=100)
    social_sentiment_raw: float = Field(ge=-1, le=1)
    cost_source_name: str
    jobs_source_name: str
    safety_source_name: str
    climate_source_name: str
    social_source_name: str

    def to_city_metrics(self) -> CityMetrics:
        return CityMetrics(
            slug=self.city_slug,
            name=self.name,
            state=self.state,
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

