from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field

ConfidenceLabel = Literal["source_backed", "estimated", "seeded", "missing"]
RANKED_DIMENSIONS = ("affordability", "job_market", "safety", "climate")
ALL_DIMENSIONS = (*RANKED_DIMENSIONS, "social")


class ScoreWeights(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    affordability: float = 0.40
    job_market: float = 0.25
    safety: float = 0.15
    climate: float = 0.10
    social_sentiment: float = 0.0

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

    def ranking_normalized(self) -> "ScoreWeights":
        return ScoreWeights(
            affordability=self.affordability,
            job_market=self.job_market,
            safety=self.safety,
            climate=self.climate,
            social_sentiment=0,
        ).normalized()


class DimensionTrust(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    confidence: ConfidenceLabel
    source: str = Field(min_length=1)
    source_date: str = Field(min_length=1)
    is_imputed: bool = False
    note: str = Field(min_length=1)


class CityMetrics(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    state: str = Field(min_length=1)
    state_code: str = Field(min_length=2, max_length=2)
    region: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    population: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    median_rent: float = Field(gt=0)
    median_home_price: float = Field(gt=0)
    median_home_price_source: str = Field(min_length=1)
    median_home_price_source_date: str = Field(min_length=1)
    median_home_price_is_imputed: bool = False
    median_income: float = Field(gt=0)
    job_growth_pct: float = Field(ge=-100, le=100)
    job_growth_source: str = Field(min_length=1)
    job_growth_source_date: str = Field(min_length=1)
    job_growth_is_imputed: bool = False
    unemployment_pct: float = Field(ge=0, le=100)
    violent_crime_per_100k: float | None = Field(default=None, ge=0)
    safety_score_raw: float = Field(ge=0, le=100)
    avg_temp_f: float | None = Field(default=None, ge=-50, le=150)
    sunny_days: float | None = Field(default=None, ge=0, le=366)
    climate_score_raw: float = Field(ge=0, le=100)
    social_sentiment_raw: float = Field(ge=-1, le=1)
    affordability_trust: DimensionTrust
    job_market_trust: DimensionTrust
    safety_trust: DimensionTrust
    climate_trust: DimensionTrust
    social_trust: DimensionTrust
    is_mvp_eligible: bool
    known_for: str = Field(min_length=1)


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

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


class ScoreDimension(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    score: float = Field(ge=0, le=10)
    confidence: ConfidenceLabel
    included_in_score: bool
    source: str = Field(min_length=1)
    source_date: str = Field(min_length=1)
    is_imputed: bool = False
    note: str = Field(min_length=1)


class ScoreContext(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    overall_confidence: ConfidenceLabel
    eligible_for_mvp_ranking: bool
    included_dimensions: List[str] = Field(default_factory=list)
    excluded_dimensions: List[str] = Field(default_factory=list)
    exclusion_reasons: List[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    beta_warning: str | None = None


class CitySummary(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    state: str = Field(min_length=1)
    state_code: str = Field(min_length=2, max_length=2)
    region: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    population: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    overall_score: float
    score_breakdown: ScoreBreakdown
    score_dimensions: List[ScoreDimension] = Field(default_factory=list)
    score_context: ScoreContext


class RedditPost(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    sentiment: str = Field(min_length=1)
    subreddit: str = Field(min_length=1)


class RedditProvenance(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subreddit: str = Field(min_length=1)
    query: str = Field(min_length=1)
    note: str = Field(min_length=1)


class RedditPanel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(min_length=1)
    confidence: ConfidenceLabel
    included_in_score: bool = False
    summary: str = Field(min_length=1)
    sentiment_score: float = Field(ge=0, le=10)
    generated_at: str = Field(min_length=1)
    lookback_days: int = Field(ge=0)
    posts_analyzed: int = Field(ge=0)
    methodology: str = Field(min_length=1)
    provenance: List[RedditProvenance] = Field(default_factory=list)
    posts: List[RedditPost] = Field(default_factory=list)


class CityDetail(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    summary: CitySummary
    metrics: CityMetrics
    highlights: List[str]
    reddit_panel: RedditPanel
