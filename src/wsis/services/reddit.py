from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from wsis.core.config import get_settings
from wsis.domain.models import CityMetrics, RedditPanel, RedditPost, RedditProvenance


class _PrecomputedRedditSummary(BaseModel):
    city_slug: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sentiment_score: float = Field(ge=0, le=10)
    generated_at: str = Field(min_length=1)
    lookback_days: int = Field(ge=0)
    posts_analyzed: int = Field(ge=0)
    methodology: str = Field(min_length=1)
    provenance: list[RedditProvenance] = Field(default_factory=list)
    posts: list[RedditPost] = Field(default_factory=list)

    def to_panel(self) -> RedditPanel:
        return RedditPanel(
            source="precomputed_city_sentiment",
            summary=self.summary,
            sentiment_score=self.sentiment_score,
            generated_at=self.generated_at,
            lookback_days=self.lookback_days,
            posts_analyzed=self.posts_analyzed,
            methodology=self.methodology,
            provenance=self.provenance,
            posts=self.posts,
        )


@lru_cache(maxsize=1)
def load_precomputed_reddit_summaries() -> dict[str, _PrecomputedRedditSummary]:
    settings = get_settings()
    path = Path(settings.reddit_sentiment_summaries_path)
    if not path.exists():
        return {}

    payload = json.loads(path.read_text())
    summaries = [_PrecomputedRedditSummary.model_validate(item) for item in payload]

    counts = Counter(summary.city_slug for summary in summaries)
    duplicates = {slug for slug, count in counts.items() if count > 1}
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate precomputed Reddit summaries found for: {duplicate_list}")

    return {summary.city_slug: summary for summary in summaries}


class RedditSentimentService(Protocol):
    def get_panel(self, city: CityMetrics) -> RedditPanel:
        """Return a city sentiment panel ready for UI rendering."""


class PrecomputedRedditSentimentService:
    """Read structured city sentiment summaries generated outside the request path."""

    def get_panel(self, city: CityMetrics) -> RedditPanel:
        summaries = load_precomputed_reddit_summaries()
        if city.slug in summaries:
            return summaries[city.slug].to_panel()

        sentiment_score = round((city.social_sentiment_raw + 1) * 5, 2)
        summary = (
            f"No structured Reddit city summary is stored for {city.name} yet. "
            "The social signal shown here is the normalized city sentiment score only."
        )
        return RedditPanel(
            source="city_profile_fallback",
            summary=summary,
            sentiment_score=sentiment_score,
            generated_at="unknown",
            lookback_days=0,
            posts_analyzed=0,
            methodology=(
                "Fallback mode: use the normalized social_sentiment_raw field from city_profiles "
                "when no precomputed Reddit summary payload is available."
            ),
            provenance=[],
            posts=[],
        )
