from wsis.domain.models import (
    CityDetail,
    CityMetrics,
    CitySummary,
    DimensionTrust,
    RedditPanel,
    ScoreBreakdown,
    ScoreContext,
    ScoreDimension,
)
from wsis.ui.decision_copy import build_decision_summary, rent_share_of_salary


def _trust(confidence: str = "source_backed") -> DimensionTrust:
    return DimensionTrust(
        confidence=confidence,
        source="acs_housing_sample",
        source_date="2024",
        is_imputed=False,
        note="Test source.",
    )


def _detail(slug: str, name: str, rent: float, temp: float, reddit_confidence: str = "seeded") -> CityDetail:
    dimensions = [
        ScoreDimension(
            key="affordability",
            label="Affordability",
            score=7,
            confidence="source_backed",
            included_in_score=True,
            source="acs_housing_sample",
            source_date="2024",
            is_imputed=False,
            note="Included.",
        ),
        ScoreDimension(
            key="social_sentiment",
            label="Social sentiment",
            score=5,
            confidence=reddit_confidence,
            included_in_score=False,
            source="reddit_placeholder_seed",
            source_date="2024",
            is_imputed=False,
            note="Context only.",
        ),
    ]
    summary = CitySummary(
        slug=slug,
        name=name,
        state="Illinois",
        state_code="IL",
        region="Midwest",
        headline="Test city.",
        population=100000,
        latitude=41,
        longitude=-87,
        overall_score=7,
        score_breakdown=ScoreBreakdown(
            affordability=7,
            job_market=7,
            safety=7,
            climate=7,
            social_sentiment=5,
            total=7,
        ),
        score_dimensions=dimensions,
        score_context=ScoreContext(
            overall_confidence="source_backed",
            eligible_for_mvp_ranking=True,
            included_dimensions=["Affordability"],
            excluded_dimensions=["Social sentiment"],
            exclusion_reasons=[],
            explanation="Test.",
        ),
    )
    metrics = CityMetrics(
        slug=slug,
        name=name,
        state="Illinois",
        state_code="IL",
        region="Midwest",
        headline="Test city.",
        population=100000,
        latitude=41,
        longitude=-87,
        median_rent=rent,
        fair_market_rent=rent,
        fair_market_rent_source="hud_fixture",
        fair_market_rent_source_date="2024",
        fair_market_rent_is_imputed=False,
        rent_to_fmr_ratio=1.0,
        practical_rent_gap=0.0,
        median_home_price=200000,
        median_home_price_source="home_price_sample",
        median_home_price_source_date="2024",
        median_home_price_is_imputed=False,
        median_income=70000,
        education_bachelors_pct=40,
        mean_commute_minutes=30,
        job_growth_pct=2,
        job_growth_source="jobs_sample",
        job_growth_source_date="2024",
        job_growth_is_imputed=False,
        unemployment_pct=4,
        violent_crime_per_100k=300,
        safety_score_raw=70,
        avg_temp_f=temp,
        sunny_days=200,
        climate_score_raw=70,
        social_sentiment_raw=0.1,
        affordability_trust=_trust(),
        job_market_trust=_trust(),
        safety_trust=_trust(),
        climate_trust=_trust(),
        social_trust=_trust(reddit_confidence),
        is_warm=temp >= 65,
        is_affordable=rent <= 1500,
        is_high_income=False,
        is_strong_job_market=False,
        is_mvp_eligible=True,
        known_for="tests",
    )
    return CityDetail(
        summary=summary,
        metrics=metrics,
        highlights=[],
        reddit_panel=RedditPanel(
            source="reddit_placeholder_seed",
            confidence=reddit_confidence,
            included_in_score=False,
            summary="Seeded context.",
            sentiment_score=5,
            generated_at="2024",
            lookback_days=30,
            posts_analyzed=5,
            methodology="seeded",
            provenance=[],
            posts=[],
        ),
    )


def test_rent_share_of_salary_uses_annual_salary() -> None:
    assert rent_share_of_salary(1_750, 70_000) == 0.3


def test_decision_keeps_looking_when_candidate_exceeds_rent_ceiling() -> None:
    chicago = _detail("chicago-il", "Chicago", 1680, 51)
    candidate = _detail("austin-tx", "Austin", 1750, 69)

    summary = build_decision_summary(
        candidate=candidate,
        baseline=chicago,
        all_details=[chicago, candidate],
        offer_salary=70_000,
        max_rent=980,
        require_warmer=True,
    )

    assert summary.verdict == "keep_looking"
    assert summary.no_rent_match is True
    assert any(issue.flag == "seeded" for issue in summary.evidence_issues)
    assert next(check for check in summary.checks if check.label == "Rent target").status == "fail"
    assert any("Raise the rent ceiling" in action for action in summary.pass_actions)


def test_decision_uses_engine_flags_for_risky_verdict() -> None:
    chicago = _detail("chicago-il", "Chicago", 1680, 51)
    candidate = _detail("pittsburgh-pa", "Pittsburgh", 900, 58)

    summary = build_decision_summary(
        candidate=candidate,
        baseline=chicago,
        all_details=[chicago, candidate],
        offer_salary=70_000,
        max_rent=980,
        require_warmer=True,
    )

    assert summary.verdict == "risky"
    assert summary.no_rent_match is False
    assert "Sarah" not in summary.headline
    assert all(check.status == "pass" for check in summary.checks)
    assert any(issue.title == "Seeded social" for issue in summary.evidence_issues)
    assert "$900 median rent" in summary.proof_points
    assert summary.pass_actions == (
        "Replace seeded or proxy evidence with source-backed data before treating this as a clean yes.",
    )


def test_civic_and_downtown_toggles_add_failed_decision_constraints() -> None:
    chicago = _detail("chicago-il", "Chicago", 1680, 51, reddit_confidence="source_backed")
    candidate = _detail("pittsburgh-pa", "Pittsburgh", 900, 58, reddit_confidence="source_backed")

    summary = build_decision_summary(
        candidate=candidate,
        baseline=chicago,
        all_details=[chicago, candidate],
        offer_salary=70_000,
        max_rent=980,
        require_warmer=True,
        require_civic_fit=True,
        require_downtown_fit=True,
    )

    checks_by_label = {check.label: check for check in summary.checks}

    assert summary.verdict == "keep_looking"
    assert checks_by_label["Civic fit"].status == "fail"
    assert checks_by_label["Civic fit"].value == "Not wired yet"
    assert checks_by_label["Downtown fit"].status == "fail"
    assert any("civic-fit signal" in action for action in summary.pass_actions)
    assert any("downtown access data" in action for action in summary.pass_actions)
