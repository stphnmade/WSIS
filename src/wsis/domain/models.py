from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ScoreWeights(BaseModel):
    affordability: float = 0.40
    job_market: float = 0.25
    safety: float = 0.15
    climate: float = 0.10
    social_sentiment: float = 0.10

    def normalized(self) -> "ScoreWeights":
        total = (
            self.affordability
            + self.job_market
            + self.safety
            + self.climate
            + self.social_sentiment
        )
        if total <= 0:
            return ScoreWeights()

        return ScoreWeights(
            affordability=self.affordability / total,
            job_market=self.job_market / total,
            safety=self.safety / total,
            climate=self.climate / total,
            social_sentiment=self.social_sentiment / total,
        )


class CityMetrics(BaseModel):
    slug: str
    name: str
    state: str
    state_code: str
    region: str
    headline: str
    population: int
    latitude: float
    longitude: float
    median_rent: float
    median_home_price: float
    median_income: float
    job_growth_pct: float
    unemployment_pct: float
    safety_score_raw: float = Field(ge=0, le=100)
    climate_score_raw: float = Field(ge=0, le=100)
    social_sentiment_raw: float = Field(ge=-1, le=1)
    known_for: str


class ScoreBreakdown(BaseModel):
    affordability: float
    job_market: float
    safety: float
    climate: float
    social_sentiment: float
    total: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "Affordability": self.affordability,
            "Job market": self.job_market,
            "Safety": self.safety,
            "Climate": self.climate,
            "Social sentiment": self.social_sentiment,
        }


class CitySummary(BaseModel):
    slug: str
    name: str
    state: str
    state_code: str
    region: str
    headline: str
    population: int
    latitude: float
    longitude: float
    overall_score: float
    score_breakdown: ScoreBreakdown


class RedditPost(BaseModel):
    title: str
    excerpt: str
    sentiment: str


class RedditPanel(BaseModel):
    source: str
    summary: str
    sentiment_score: float
    posts: List[RedditPost]


class CityDetail(BaseModel):
    summary: CitySummary
    metrics: CityMetrics
    highlights: List[str]
    reddit_panel: RedditPanel

