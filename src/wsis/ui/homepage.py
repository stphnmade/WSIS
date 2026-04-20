from __future__ import annotations

from statistics import fmean

from wsis.domain.models import CityDetail, CitySummary, ScoreWeights


WEIGHT_PRODUCT_LABELS = {
    "affordability": "affordability",
    "job_market": "job market strength",
    "safety": "safety",
    "climate": "climate comfort",
}

WEIGHT_REASON_PHRASES = {
    "affordability": "lower rent burden and less aggressive housing pressure",
    "job_market": "stronger employment metrics and career upside",
    "safety": "safer peer-set conditions",
    "climate": "warmer or more comfortable climate signals",
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

# These are intentionally lightweight heuristic filters until WSIS models sector, civic,
# and ideology-specific datasets explicitly.
CONSUMER_FILTERS = (
    {
        "key": "warm_weather",
        "label": "Warm Weather",
        "description": "Favor cities with stronger climate comfort or warmer temperature signals.",
        "placeholder": False,
    },
    {
        "key": "affordable",
        "label": "Affordable",
        "description": "Favor cities with lower rent burden or stronger affordability scores.",
        "placeholder": False,
    },
    {
        "key": "high_earning_potential",
        "label": "High Earning Potential",
        "description": "Favor stronger incomes and job-market upside.",
        "placeholder": False,
    },
    {
        "key": "tech_focus",
        "label": "Tech Focus",
        "description": "Heuristic filter favoring cities with tech-oriented income and job signals.",
        "placeholder": True,
    },
    {
        "key": "agriculture_industry_focus",
        "label": "Agriculture/Industry Focus",
        "description": "Heuristic filter favoring lower-cost Midwestern or Southern labor markets.",
        "placeholder": True,
    },
    {
        "key": "republican_leaning",
        "label": "Republican-Leaning",
        "description": "Placeholder civic signal based on broad state-level assumptions.",
        "placeholder": True,
    },
    {
        "key": "democratic_leaning",
        "label": "Democratic-Leaning",
        "description": "Placeholder civic signal based on broad state-level assumptions.",
        "placeholder": True,
    },
)

REPUBLICAN_PLACEHOLDER_STATES = {"TX", "FL", "NC"}
DEMOCRATIC_PLACEHOLDER_STATES = {"WA", "IL", "MN", "CO", "PA", "WI"}

STARTER_BASELINE_WEIGHTS = {
    "affordability": 0.30,
    "job_market": 0.34,
    "safety": 0.20,
    "climate": 0.16,
}

REGION_MAP_FOCUS = {
    "All": {"lat": 38.2, "lon": -96.2, "scale": 1.02, "mode": "national"},
    "West": {"lat": 39.2, "lon": -111.3, "scale": 1.45, "mode": "region"},
    "Midwest": {"lat": 41.6, "lon": -90.3, "scale": 1.65, "mode": "region"},
    "South": {"lat": 34.2, "lon": -84.6, "scale": 1.55, "mode": "region"},
    "Northeast": {"lat": 41.1, "lon": -74.9, "scale": 2.35, "mode": "region"},
}

STATE_CODE_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
    "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17",
    "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31",
    "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}


def strongest_dimensions(summary: CitySummary, include_context: bool = False) -> list[tuple[str, float]]:
    items = summary.score_breakdown.as_dict().items()
    if not include_context:
        included_labels = set(summary.score_context.included_dimensions)
        items = [(label, score) for label, score in items if label in included_labels]
        if not items:
            items = list(summary.score_breakdown.as_dict().items())
    return sorted(items, key=lambda item: item[1], reverse=True)


def best_places_to_start_score(detail: CityDetail, weights: ScoreWeights) -> float:
    active_weights = weights.ranking_normalized().model_dump()
    blended_weights = {
        key: (active_weights[key] + STARTER_BASELINE_WEIGHTS[key]) / 2
        for key in STARTER_BASELINE_WEIGHTS
    }
    weight_total = sum(blended_weights.values())
    breakdown = detail.summary.score_breakdown
    score = (
        breakdown.affordability * blended_weights["affordability"]
        + breakdown.job_market * blended_weights["job_market"]
        + breakdown.safety * blended_weights["safety"]
        + breakdown.climate * blended_weights["climate"]
    ) / weight_total
    return round(score, 2)


def aggregate_state_start_scores(
    details: list[CityDetail],
    weights: ScoreWeights,
) -> list[dict[str, object]]:
    state_rows: dict[tuple[str, str], list[dict[str, object]]] = {}
    for detail in details:
        state_key = (detail.summary.state_code, detail.summary.state)
        state_rows.setdefault(state_key, []).append(
            {
                "detail": detail,
                "start_score": best_places_to_start_score(detail, weights),
            }
        )

    aggregates: list[dict[str, object]] = []
    for (state_code, state_name), rows in state_rows.items():
        total_population = sum(item["detail"].summary.population for item in rows)
        if total_population > 0:
            weighted_score = sum(
                item["start_score"] * item["detail"].summary.population for item in rows
            ) / total_population
        else:
            weighted_score = fmean(item["start_score"] for item in rows)
        top_city_row = max(rows, key=lambda item: item["start_score"])
        aggregates.append(
            {
                "state_code": state_code,
                "state": state_name,
                "start_score": round(weighted_score, 2),
                "top_city": top_city_row["detail"].summary.name,
                "city_count": len(rows),
            }
        )

    return sorted(aggregates, key=lambda row: float(row["start_score"]), reverse=True)


def labeled_city_slugs(
    details: list[CityDetail],
    weights: ScoreWeights,
    selected_region: str,
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
) -> set[str]:
    if selected_detail is not None:
        slugs = {selected_detail.summary.slug}
        slugs.update(detail.summary.slug for detail in compare_details)
        same_state = [
            detail
            for detail in details
            if detail.summary.state_code == selected_detail.summary.state_code
            and detail.summary.slug not in slugs
        ]
        for detail in sorted(
            same_state,
            key=lambda row: best_places_to_start_score(row, weights),
            reverse=True,
        )[:2]:
            slugs.add(detail.summary.slug)
        return slugs

    if len(compare_details) >= 2:
        slugs = {detail.summary.slug for detail in compare_details}
        for detail in sorted(
            details,
            key=lambda row: best_places_to_start_score(row, weights),
            reverse=True,
        )[:2]:
            slugs.add(detail.summary.slug)
        return slugs

    label_budget = 6 if selected_region != "All" else 4
    return {
        detail.summary.slug
        for detail in sorted(
            details,
            key=lambda row: best_places_to_start_score(row, weights),
            reverse=True,
        )[:label_budget]
    }


def map_focus_config(
    selected_region: str,
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
) -> dict[str, float | str]:
    if selected_detail is not None:
        return {
            "lat": selected_detail.summary.latitude,
            "lon": selected_detail.summary.longitude,
            "scale": 4.8,
            "mode": "inspect",
        }

    if len(compare_details) >= 2:
        return {
            "lat": fmean(detail.summary.latitude for detail in compare_details),
            "lon": fmean(detail.summary.longitude for detail in compare_details),
            "scale": 2.2,
            "mode": "compare",
        }

    return REGION_MAP_FOCUS.get(selected_region, REGION_MAP_FOCUS["All"])


def interaction_stage_copy(
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
) -> tuple[str, str]:
    if selected_detail is None and len(compare_details) < 2:
        return (
            "Discovery mode",
            "Read state shading first, then click a city when something looks worth inspecting.",
        )
    if selected_detail is not None and len(compare_details) < 2:
        return (
            f"Inspecting {selected_detail.summary.name}, {selected_detail.summary.state_code}",
            "Keep this city in the side panel, then add it to compare only if it still feels plausible.",
        )
    if selected_detail is not None:
        return (
            f"Inspecting {selected_detail.summary.name}, {selected_detail.summary.state_code}",
            "Compare tray is active. Keep clicking cities to inspect them without losing the shortlist you locked in.",
        )
    return (
        "Compare mode",
        "Two or more cities are locked in below. Click any point to inspect it while keeping the tray intact.",
    )


def county_overlay_state_codes(
    details: list[CityDetail],
    selected_region: str,
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
) -> set[str]:
    if selected_detail is not None:
        return {selected_detail.summary.state_code}

    if len(compare_details) >= 2:
        return {detail.summary.state_code for detail in compare_details}

    if selected_region != "All":
        return {detail.summary.state_code for detail in details}

    return set()


def county_overlay_state_fips(
    details: list[CityDetail],
    selected_region: str,
    selected_detail: CityDetail | None,
    compare_details: list[CityDetail],
) -> set[str]:
    return {
        STATE_CODE_TO_FIPS[state_code]
        for state_code in county_overlay_state_codes(details, selected_region, selected_detail, compare_details)
        if state_code in STATE_CODE_TO_FIPS
    }


def ranking_explanation(weights: ScoreWeights) -> str:
    ordered = sorted(
        weights.ranking_normalized().model_dump().items(),
        key=lambda item: item[1],
        reverse=True,
    )
    primary_key, _ = ordered[0]
    secondary_key, _ = ordered[1]
    return (
        f"Your current ranking emphasizes {WEIGHT_PRODUCT_LABELS[primary_key]} and "
        f"{WEIGHT_PRODUCT_LABELS[secondary_key]}, so cities with "
        f"{WEIGHT_REASON_PHRASES[primary_key]} and {WEIGHT_REASON_PHRASES[secondary_key]} "
        "are surfacing higher. Social sentiment is shown separately as context and does not affect the rank."
    )


def city_reason_snippet(detail: CityDetail, weights: ScoreWeights) -> str:
    top_dimensions = strongest_dimensions(detail.summary)[:2]
    dimension_labels = " and ".join(label.lower() for label, _ in top_dimensions) or "the available trusted dimensions"
    lead_weights = sorted(
        weights.ranking_normalized().model_dump().items(),
        key=lambda item: item[1],
        reverse=True,
    )[:2]
    lead_weight_labels = " and ".join(WEIGHT_PRODUCT_LABELS[name] for name, _ in lead_weights)
    return (
        f"{detail.summary.name} is surfacing because it combines {dimension_labels} "
        f"under a ranking mix currently tilted toward {lead_weight_labels}."
    )


def badge_labels(detail: CityDetail) -> list[str]:
    breakdown = detail.summary.score_breakdown
    badges: list[str] = []

    if breakdown.affordability >= 7 or rent_burden(detail) <= 0.25:
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

    top_dimensions = strongest_dimensions(detail.summary, include_context=True)[:2]
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


def rent_burden(detail: CityDetail) -> float:
    return (detail.metrics.median_rent * 12) / detail.metrics.median_income


def standout_attribute(detail: CityDetail) -> str:
    badges = badge_labels(detail)
    if badges:
        return badges[0]
    label, score = strongest_dimensions(detail.summary)[0]
    return f"{label} {score}/10"


def quick_stats(detail: CityDetail) -> list[tuple[str, str]]:
    return [
        ("Median rent", f"${detail.metrics.median_rent:,.0f}"),
        ("Median income", f"${detail.metrics.median_income:,.0f}"),
        ("Unemployment", f"{detail.metrics.unemployment_pct:.1f}%"),
        ("Sentiment", f"{detail.reddit_panel.sentiment_score:.1f}"),
    ]


def consumer_filter_labels() -> list[str]:
    return [option["label"] for option in CONSUMER_FILTERS]


def filter_option_by_label(label: str) -> dict[str, object]:
    return next(option for option in CONSUMER_FILTERS if option["label"] == label)


def active_filter_descriptions(selected_filters: list[str]) -> list[str]:
    descriptions: list[str] = []
    for label in selected_filters:
        option = filter_option_by_label(label)
        description = str(option["description"])
        if bool(option["placeholder"]):
            description += " Placeholder logic for now."
        descriptions.append(description)
    return descriptions


def filter_matches(detail: CityDetail, filter_key: str) -> bool:
    if filter_key == "warm_weather":
        return detail.summary.score_breakdown.climate >= 7 or (detail.metrics.avg_temp_f or 0) >= 65
    if filter_key == "affordable":
        return detail.summary.score_breakdown.affordability >= 7 or rent_burden(detail) <= 0.25
    if filter_key == "high_earning_potential":
        return detail.metrics.median_income >= 85000 or detail.summary.score_breakdown.job_market >= 7
    if filter_key == "tech_focus":
        return detail.metrics.median_income >= 90000 and detail.summary.score_breakdown.job_market >= 7
    if filter_key == "agriculture_industry_focus":
        return detail.summary.region in {"Midwest", "South"} and detail.metrics.median_home_price <= 450000
    if filter_key == "republican_leaning":
        return detail.summary.state_code in REPUBLICAN_PLACEHOLDER_STATES
    if filter_key == "democratic_leaning":
        return detail.summary.state_code in DEMOCRATIC_PLACEHOLDER_STATES
    return True


def apply_consumer_filters(
    details: list[CityDetail],
    selected_region: str,
    selected_filters: list[str],
) -> list[CityDetail]:
    filtered = [
        detail
        for detail in details
        if selected_region == "All" or detail.summary.region == selected_region
    ]
    for label in selected_filters:
        option = filter_option_by_label(label)
        filtered = [detail for detail in filtered if filter_matches(detail, str(option["key"]))]
    return filtered
