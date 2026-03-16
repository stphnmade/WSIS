from __future__ import annotations

from typing import Protocol

from wsis.domain.models import CityMetrics, RedditPanel, RedditPost


class RedditSentimentService(Protocol):
    def get_panel(self, city: CityMetrics) -> RedditPanel:
        """Return a city sentiment panel ready for UI rendering."""


class PlaceholderRedditSentimentService:
    """Deterministic placeholder until a real Reddit pipeline exists."""

    def get_panel(self, city: CityMetrics) -> RedditPanel:
        sentiment_score = round((city.social_sentiment_raw + 1) * 5, 2)
        sentiment_label = "positive" if sentiment_score >= 6.5 else "mixed"

        summary = (
            f"Placeholder Reddit read for {city.name}: posters describe the city as "
            f"{sentiment_label}, with recurring themes around {city.known_for}. "
            "This module is stubbed for now and should be replaced by a real "
            "pipeline that handles subreddit selection, filtering, and moderation."
        )

        posts = [
            RedditPost(
                title=f"Thinking about moving to {city.name}",
                excerpt=(
                    f"Common discussion themes mention {city.known_for} and whether the "
                    "career upside offsets the local cost structure."
                ),
                sentiment=sentiment_label,
            ),
            RedditPost(
                title=f"What surprised you after living in {city.name} for a year?",
                excerpt=(
                    "People consistently talk about neighborhood fit, daily pace, and how "
                    "easy it is to build a social life after relocating."
                ),
                sentiment="mixed",
            ),
        ]

        return RedditPanel(
            source="placeholder",
            summary=summary,
            sentiment_score=sentiment_score,
            posts=posts,
        )

