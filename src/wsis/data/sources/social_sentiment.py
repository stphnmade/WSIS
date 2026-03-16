from __future__ import annotations

from pathlib import Path

from wsis.data.models import SocialSentimentRecord
from wsis.data.sources.base import load_csv_records


def load_social_sentiment(path: Path) -> tuple[SocialSentimentRecord, ...]:
    return load_csv_records(path, SocialSentimentRecord)

