from __future__ import annotations

from wsis.domain.models import CityDetail, CitySummary, ScoreWeights


WEIGHT_PRODUCT_LABELS = {
    "affordability": "affordability",
    "job_market": "job market strength",
    "safety": "safety",
    "climate": "climate comfort",
    "social_sentiment": "social momentum",
}

WEIGHT_REASON_PHRASES = {
    "affordability": "lower rent burden and less aggressive housing pressure",
    "job_market": "stronger employment metrics and career upside",
    "safety": "safer peer-set conditions",
    "climate": "warmer or more comfortable climate signals",
    "social_sentiment": "better social buzz and city sentiment",
}

THEME_PATTERNS = (
    ("cost pressure", ("rent", "cost", "afford", "price", "budget", "housing costs")),
    ("career upside", ("job", "jobs", "hiring", "career", "salary", "tech", "employment")),
    ("social life", ("social", "friends", "nightlife", "community", "meeting people")),
    ("weather", ("weather", "winter", "summer", "sun", "sunshine", "climate", "heat")),
    ("getting around", ("traffic", "commute", "transit", "driving", "bike", "walk")),
    ("neighborhood fit", ("neighborhood", "housing", "apartment", "area", "district")),
    ("outdoor access", ("outdoor", "nature", "mountain", "lake", "waterfront", "park")),
)


def strongest_dimensions(summary: CitySummary) -> list[tuple[str, float]]:
    return sorted(summary.score_breakdown.as_dict().items(), key=lambda item: item[1], reverse=True)


def ranking_explanation(weights: ScoreWeights) -> str:
    ordered = sorted(
        weights.normalized().model_dump().items(),
        key=lambda item: item[1],
        reverse=True,
    )
    primary_key, _ = ordered[0]
    secondary_key, _ = ordered[1]
    return (
        f"Your current ranking emphasizes {WEIGHT_PRODUCT_LABELS[primary_key]} and "
        f"{WEIGHT_PRODUCT_LABELS[secondary_key]}, so cities with "
        f"{WEIGHT_REASON_PHRASES[primary_key]} and {WEIGHT_REASON_PHRASES[secondary_key]} "
        "are surfacing higher."
    )


def city_reason_snippet(detail: CityDetail, weights: ScoreWeights) -> str:
    top_dimensions = strongest_dimensions(detail.summary)[:2]
    dimension_labels = " and ".join(label.lower() for label, _ in top_dimensions)
    lead_weights = sorted(
        weights.normalized().model_dump().items(),
        key=lambda item: item[1],
        reverse=True,
    )[:2]
    lead_weight_labels = " and ".join(WEIGHT_PRODUCT_LABELS[name] for name, _ in lead_weights)
    return (
        f"{detail.summary.name} is staying competitive because it combines {dimension_labels} "
        f"under a ranking model currently tilted toward {lead_weight_labels}."
    )


def badge_labels(detail: CityDetail) -> list[str]:
    breakdown = detail.summary.score_breakdown
    badges: list[str] = []

    if breakdown.affordability >= 7 or (detail.metrics.median_rent * 12 / detail.metrics.median_income) <= 0.25:
        badges.append("Affordable")
    if breakdown.job_market >= 7:
        badges.append("Strong Jobs")
    if detail.metrics.unemployment_pct <= 3.3:
        badges.append("Lower Unemployment")
    if breakdown.climate >= 7 or (detail.metrics.avg_temp_f or 0) >= 65:
        badges.append("Warmer Climate")
    if breakdown.social_sentiment >= 6.5 or detail.reddit_panel.sentiment_score >= 6.5:
        badges.append("Social Buzz")
    if breakdown.safety >= 7:
        badges.append("Safer Feel")

    if not badges:
        badges.append(detail.summary.region)

    return badges[:3]


def social_themes(detail: CityDetail) -> list[str]:
    text_blocks = [detail.reddit_panel.summary]
    text_blocks.extend(post.excerpt for post in detail.reddit_panel.posts[:3])
    lowered = " ".join(text_blocks).lower()

    matches: list[str] = []
    for label, patterns in THEME_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            matches.append(label)

    if matches:
        return matches[:3]

    top_dimensions = strongest_dimensions(detail.summary)[:2]
    fallback = []
    for label, _ in top_dimensions:
        if label == "Affordability":
            fallback.append("cost pressure")
        elif label == "Job market":
            fallback.append("career upside")
        elif label == "Climate":
            fallback.append("weather")
        elif label == "Social sentiment":
            fallback.append("social life")
        elif label == "Safety":
            fallback.append("neighborhood fit")
    deduped: list[str] = []
    for label in fallback:
        if label not in deduped:
            deduped.append(label)
    return deduped[:3]


def social_excerpt(detail: CityDetail) -> str:
    if detail.reddit_panel.posts:
        return detail.reddit_panel.posts[0].excerpt
    return (
        f"WSIS has a score-level social signal for {detail.summary.name}, but not a richer thread excerpt yet."
    )


def social_preview_title(detail: CityDetail) -> str:
    if detail.reddit_panel.posts:
        return detail.reddit_panel.posts[0].title
    return f"{detail.summary.name} social preview"


def comparison_preview_rows(details: list[CityDetail]) -> list[dict[str, object]]:
    return [
        {
            "City": f"{detail.summary.name}, {detail.summary.state_code}",
            "Overall": detail.summary.overall_score,
            "Median rent": f"${detail.metrics.median_rent:,.0f}",
            "Median income": f"${detail.metrics.median_income:,.0f}",
            "Unemployment": f"{detail.metrics.unemployment_pct:.1f}%",
            "Sentiment": detail.reddit_panel.sentiment_score,
        }
        for detail in details
    ]
