from wsis.domain.models import (
    CityDetail,
    CityMetrics,
    CitySummary,
    DimensionTrust,
    RedditPanel,
    RedditPost,
    ScoreBreakdown,
    ScoreContext,
    ScoreDimension,
    ScoreWeights,
)
from wsis.ui.homepage import (
    active_filter_descriptions,
    apply_consumer_filters,
    badge_labels,
    best_places_to_start_score,
    city_reason_snippet,
    comparison_preview_rows,
    county_overlay_state_fips,
    interaction_stage_copy,
    labeled_city_slugs,
    map_focus_config,
    quick_stats,
    ranking_explanation,
    social_excerpt,
    aggregate_state_start_scores,
    standout_attribute,
    social_themes,
)


def _detail() -> CityDetail:
    dimensions = [
        ScoreDimension(
            key="affordability",
            label="Affordability",
            score=7.2,
            confidence="source_backed",
            included_in_score=True,
            source="census_acs_city_metrics",
            source_date="2026-04-20",
            is_imputed=False,
            note="Included in score.",
        ),
        ScoreDimension(
            key="job_market",
            label="Job market",
            score=8.4,
            confidence="source_backed",
            included_in_score=True,
            source="bls_county_unemployment",
            source_date="2026-04-20",
            is_imputed=False,
            note="Included in score.",
        ),
        ScoreDimension(
            key="safety",
            label="Safety",
            score=6.3,
            confidence="source_backed",
            included_in_score=True,
            source="fbi_county_crime",
            source_date="2026-04-20",
            is_imputed=False,
            note="Included in score.",
        ),
        ScoreDimension(
            key="climate",
            label="Climate",
            score=7.5,
            confidence="source_backed",
            included_in_score=True,
            source="noaa_county_climate",
            source_date="2026-04-20",
            is_imputed=False,
            note="Included in score.",
        ),
        ScoreDimension(
            key="social_sentiment",
            label="Social sentiment",
            score=7.1,
            confidence="seeded",
            included_in_score=False,
            source="seeded_reddit_placeholder",
            source_date="2026-04-20",
            is_imputed=False,
            note="Context only.",
        ),
    ]
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
            score_dimensions=dimensions,
            score_context=ScoreContext(
                overall_confidence="source_backed",
                eligible_for_mvp_ranking=True,
                included_dimensions=["Affordability", "Job market", "Safety", "Climate"],
                excluded_dimensions=["Social sentiment"],
                explanation="Trust-first MVP score.",
                beta_warning=None,
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
            fair_market_rent=1710,
            fair_market_rent_source="hud_fair_market_rents_2br",
            fair_market_rent_source_date="2026-04-20",
            fair_market_rent_is_imputed=False,
            rent_to_fmr_ratio=1.0234,
            practical_rent_gap=40,
            median_home_price=525000,
            median_home_price_source="cost_of_living_sample",
            median_home_price_source_date="2026-04-20",
            median_home_price_is_imputed=False,
            median_income=92000,
            education_bachelors_pct=58.0,
            mean_commute_minutes=25.9,
            job_growth_pct=4.8,
            job_growth_source="jobs_sample",
            job_growth_source_date="2026-04-20",
            job_growth_is_imputed=False,
            unemployment_pct=3.1,
            violent_crime_per_100k=420,
            safety_score_raw=66,
            avg_temp_f=69,
            sunny_days=228,
            climate_score_raw=78,
            social_sentiment_raw=0.42,
            affordability_trust=DimensionTrust(
                confidence="source_backed",
                source="census_acs_city_metrics",
                source_date="2026-04-20",
                is_imputed=False,
                note="Included in score.",
            ),
            job_market_trust=DimensionTrust(
                confidence="source_backed",
                source="bls_county_unemployment",
                source_date="2026-04-20",
                is_imputed=False,
                note="Included in score.",
            ),
            safety_trust=DimensionTrust(
                confidence="source_backed",
                source="fbi_county_crime",
                source_date="2026-04-20",
                is_imputed=False,
                note="Included in score.",
            ),
            climate_trust=DimensionTrust(
                confidence="source_backed",
                source="noaa_county_climate",
                source_date="2026-04-20",
                is_imputed=False,
                note="Included in score.",
            ),
            social_trust=DimensionTrust(
                confidence="seeded",
                source="seeded_reddit_placeholder",
                source_date="2026-04-20",
                is_imputed=False,
                note="Context only.",
            ),
            is_warm=True,
            is_affordable=True,
            is_high_income=True,
            is_strong_job_market=True,
            is_mvp_eligible=True,
            known_for="tech hiring, live music, warm weather",
        ),
        highlights=[],
        reddit_panel=RedditPanel(
            source="precomputed_city_sentiment",
            confidence="seeded",
            included_in_score=False,
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
            social_sentiment=0,
        )
    )

    assert "affordability" in explanation
    assert "job market strength" in explanation
    assert "does not affect the rank" in explanation


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


def test_best_places_to_start_score_and_state_aggregation() -> None:
    detail = _detail()
    state_rows = aggregate_state_start_scores([detail], ScoreWeights())

    assert best_places_to_start_score(detail, ScoreWeights()) >= 7
    assert state_rows[0]["state_code"] == "TX"
    assert state_rows[0]["top_city"] == "Austin"


def test_label_density_focus_and_interaction_stage_copy() -> None:
    detail = _detail()
    label_slugs = labeled_city_slugs(
        [detail],
        ScoreWeights(),
        "South",
        detail,
        [],
    )
    focus = map_focus_config("South", detail, [])
    stage_title, stage_body = interaction_stage_copy(detail, [])

    assert "austin-tx" in label_slugs
    assert focus["mode"] == "inspect"
    assert "Inspecting Austin" in stage_title
    assert "add it to compare" in stage_body


def test_county_overlay_state_fips_stays_scoped() -> None:
    detail = _detail()

    assert county_overlay_state_fips([detail], "All", None, []) == set()
    assert county_overlay_state_fips([detail], "South", None, []) == {"48"}
    assert county_overlay_state_fips([detail], "All", detail, []) == {"48"}
