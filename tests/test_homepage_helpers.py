from wsis.domain.models import (
    CityDetail,
    CityMetrics,
    CitySummary,
    RedditPanel,
    RedditPost,
    ScoreBreakdown,
    ScoreWeights,
)
from wsis.ui.homepage import (
    active_filter_descriptions,
    apply_consumer_filters,
    badge_labels,
    city_reason_snippet,
    comparison_preview_rows,
    quick_stats,
    ranking_explanation,
    social_excerpt,
    standout_attribute,
    social_themes,
)


def _detail() -> CityDetail:
    return CityDetail(
        summary=CitySummary(
            slug="austin-tx",
            name="Austin",
            state="Texas",
            state_code="TX",
            region="South",
            headline="Fast-growing job hub with strong social energy.",
            population=979882,
            latitude=30.2672,
            longitude=-97.7431,
            overall_score=7.9,
            score_breakdown=ScoreBreakdown(
                affordability=7.2,
                job_market=8.4,
                safety=6.3,
                climate=7.5,
                social_sentiment=7.1,
                total=7.9,
            ),
        ),
        metrics=CityMetrics(
            slug="austin-tx",
            name="Austin",
            state="Texas",
            state_code="TX",
            region="South",
            headline="Fast-growing job hub with strong social energy.",
            population=979882,
            latitude=30.2672,
            longitude=-97.7431,
            median_rent=1750,
            median_home_price=525000,
            median_income=92000,
            job_growth_pct=4.8,
            unemployment_pct=3.1,
            violent_crime_per_100k=420,
            safety_score_raw=66,
            avg_temp_f=69,
            sunny_days=228,
            climate_score_raw=78,
            social_sentiment_raw=0.42,
            known_for="tech hiring, live music, warm weather",
        ),
        highlights=[],
        reddit_panel=RedditPanel(
            source="precomputed_city_sentiment",
            summary="Posters mention jobs, rent pressure, traffic, and social life.",
            sentiment_score=7.1,
            generated_at="2026-04-10",
            lookback_days=120,
            posts_analyzed=36,
            methodology="seeded",
            provenance=[],
            posts=[
                RedditPost(
                    title="Moving to Austin in my mid-20s",
                    excerpt="Jobs and social life are a draw, but rent and traffic come up in nearly every thread.",
                    sentiment="mostly positive",
                    subreddit="r/Austin",
                )
            ],
        ),
    )


def test_ranking_explanation_uses_top_weights() -> None:
    explanation = ranking_explanation(
        ScoreWeights(
            affordability=40,
            job_market=25,
            safety=15,
            climate=10,
            social_sentiment=10,
        )
    )

    assert "affordability" in explanation
    assert "job market strength" in explanation


def test_badge_labels_use_metrics_and_social_signal() -> None:
    badges = badge_labels(_detail())

    assert "Affordable" in badges
    assert "Strong Jobs" in badges
    assert "Lower Unemployment" in badges or "Social Buzz" in badges


def test_social_helpers_extract_themes_and_excerpt() -> None:
    detail = _detail()

    themes = social_themes(detail)

    assert "career upside" in themes
    assert "cost pressure" in themes
    assert "social life" in themes
    assert "rent and traffic" in social_excerpt(detail)


def test_city_reason_snippet_and_comparison_rows() -> None:
    detail = _detail()
    reason = city_reason_snippet(detail, ScoreWeights())
    rows = comparison_preview_rows([detail])

    assert "Austin is surfacing" in reason
    assert rows[0]["City"] == "Austin, TX"
    assert rows[0]["Median rent"] == "$1,750"


def test_standout_attribute_and_quick_stats_are_readable() -> None:
    detail = _detail()

    assert standout_attribute(detail) in {"Affordable", "Strong Jobs", "Lower Unemployment"}
    stats = quick_stats(detail)
    assert stats[0] == ("Median rent", "$1,750")
    assert stats[3] == ("Sentiment", "7.1")


def test_apply_consumer_filters_uses_region_and_human_filters() -> None:
    detail = _detail()

    filtered = apply_consumer_filters([detail], "South", ["Warm Weather", "High Earning Potential"])
    assert filtered == [detail]

    excluded = apply_consumer_filters([detail], "Midwest", [])
    assert excluded == []


def test_active_filter_descriptions_marks_placeholder_filters() -> None:
    descriptions = active_filter_descriptions(["Tech Focus", "Affordable"])

    assert "Placeholder logic for now." in descriptions[0]
    assert "Placeholder logic for now." not in descriptions[1]
