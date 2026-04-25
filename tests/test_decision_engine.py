from datetime import date

from wsis.decision import DecisionInputs, build_relocation_decisions
from wsis.domain.models import CityMetrics, DimensionTrust


def _trust(confidence: str = "source_backed", source_date: str = "2026-01-01") -> DimensionTrust:
    return DimensionTrust(
        confidence=confidence,
        source="test_fixture",
        source_date=source_date,
        is_imputed=confidence in {"estimated", "seeded"},
        note="Test trust record.",
    )


def _city(
    slug: str,
    *,
    median_rent: float = 1800,
    avg_temp_f: float = 70,
    social_confidence: str = "source_backed",
    safety_source_date: str = "2026-01-01",
    job_confidence: str = "source_backed",
    job_source_date: str = "2026-01-01",
) -> CityMetrics:
    return CityMetrics(
        slug=slug,
        name=slug.replace("-", " ").title(),
        state="Texas",
        state_code="TX",
        region="South",
        headline="Test city",
        population=100000,
        latitude=30,
        longitude=-97,
        median_rent=median_rent,
        median_home_price=350000,
        median_home_price_source="test_fixture",
        median_home_price_source_date="2026-01-01",
        median_home_price_is_imputed=False,
        median_income=90000,
        job_growth_pct=2.5,
        job_growth_source="test_fixture",
        job_growth_source_date=job_source_date,
        job_growth_is_imputed=job_confidence == "estimated",
        unemployment_pct=4.2,
        violent_crime_per_100k=350,
        safety_score_raw=72,
        avg_temp_f=avg_temp_f,
        sunny_days=230,
        climate_score_raw=74,
        social_sentiment_raw=0.2,
        affordability_trust=_trust(),
        job_market_trust=_trust(job_confidence, job_source_date),
        safety_trust=_trust(source_date=safety_source_date),
        climate_trust=_trust(),
        social_trust=_trust(social_confidence),
        is_mvp_eligible=True,
        known_for="Test data",
    )


def test_david_hard_rent_target_fails_when_no_candidate_meets_it() -> None:
    baseline = _city("baseline-tx", median_rent=1600, avg_temp_f=65)
    candidates = [
        _city("too-expensive-a", median_rent=2200, avg_temp_f=72),
        _city("too-expensive-b", median_rent=2400, avg_temp_f=75),
    ]
    inputs = DecisionInputs(
        baseline_city_slug="baseline-tx",
        offer_salary=120000,
        max_rent=2000,
        require_warmer_than_baseline=True,
    )

    run = build_relocation_decisions([baseline, *candidates], inputs, dataset_count=20)

    assert {decision.verdict for decision in run.decisions} == {"Keep looking"}
    assert all(
        not next(
            check for check in decision.constraints if check.key == "max_rent"
        ).passed
        for decision in run.decisions
    )
    assert all("median rent vs $2,000 max rent" in decision.constraints[0].evidence for decision in run.decisions)


def test_candidate_failing_max_rent_cannot_receive_take_it() -> None:
    baseline = _city("chicago-il", median_rent=980, avg_temp_f=51)
    candidate = _city("warm-city", median_rent=1100, avg_temp_f=70)
    inputs = DecisionInputs(
        baseline_city_slug="chicago-il",
        candidate_city_slugs=["warm-city"],
        offer_salary=70000,
        max_rent=980,
        require_warmer_than_baseline=True,
    )

    run = build_relocation_decisions(
        [baseline, candidate],
        inputs,
        dataset_count=20,
        as_of=date(2026, 4, 24),
    )

    decision = run.decisions[0]
    rent_check = next(check for check in decision.constraints if check.key == "max_rent")
    assert rent_check.passed is False
    assert decision.verdict != "Take it"
    assert decision.verdict == "Keep looking"


def test_sarah_flags_seeded_proxy_and_limited_data() -> None:
    baseline = _city("baseline-tx", median_rent=1500, avg_temp_f=62)
    candidate = _city(
        "seeded-city",
        median_rent=1700,
        avg_temp_f=70,
        social_confidence="seeded",
        safety_source_date="2023-01-01",
        job_confidence="estimated",
        job_source_date="unknown",
    )
    inputs = DecisionInputs(
        baseline_city_slug="baseline-tx",
        offer_salary=120000,
        max_rent=2000,
        require_warmer_than_baseline=True,
    )

    run = build_relocation_decisions(
        [baseline, candidate],
        inputs,
        dataset_count=2,
        as_of=date(2026, 4, 24),
    )

    decision = run.decisions[0]
    flag_keys = {flag.key for flag in decision.skeptic_flags}

    assert decision.verdict == "Viable but risky"
    assert "limited_dataset" in flag_keys
    assert "seeded_social" in flag_keys
    assert "proxy_job_market" in flag_keys
    assert "proxy_job_growth" in flag_keys
    assert "stale_safety_source_date" in flag_keys
    assert "unknown_job_market_source_date" in flag_keys
    assert "unknown_job_growth_date" in flag_keys


def test_decision_engine_limits_run_to_requested_candidates() -> None:
    baseline = _city("chicago-il")
    requested = _city("tampa-fl")
    omitted = _city("denver-co")
    inputs = DecisionInputs(
        baseline_city_slug="chicago-il",
        candidate_city_slugs=["tampa-fl"],
        offer_salary=70000,
        max_rent=980,
        require_warmer_than_baseline=True,
    )

    run = build_relocation_decisions(
        [baseline, requested, omitted],
        inputs,
        dataset_count=20,
    )

    assert run.candidate_count == 1
    assert [decision.city_slug for decision in run.decisions] == ["tampa-fl"]
