from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from wsis.decision.models import (
    ConstraintCheck,
    DecisionInputs,
    DecisionRun,
    RelocationDecision,
    SkepticFlag,
    Verdict,
)
from wsis.domain.models import CityDetail, CityMetrics, DimensionTrust


def build_relocation_decisions(
    cities: Iterable[CityMetrics | CityDetail],
    inputs: DecisionInputs,
    *,
    dataset_count: int | None = None,
    as_of: date | None = None,
) -> DecisionRun:
    """Evaluate candidate cities against hard relocation constraints."""

    metrics = [_as_metrics(city) for city in cities]
    by_slug = {city.slug: city for city in metrics}
    baseline = by_slug.get(inputs.baseline_city_slug)
    if baseline is None:
        raise ValueError(f"Baseline city not found: {inputs.baseline_city_slug}")

    candidates = _candidate_cities(metrics, by_slug, inputs)
    count_for_flags = dataset_count if dataset_count is not None else len(metrics)
    decisions = [
        _build_city_decision(
            city,
            baseline,
            inputs,
            dataset_count=count_for_flags,
            as_of=as_of or date.today(),
        )
        for city in candidates
    ]

    return DecisionRun(
        baseline_city_slug=baseline.slug,
        baseline_city_name=baseline.name,
        candidate_count=len(candidates),
        decisions=decisions,
    )


def _candidate_cities(
    metrics: list[CityMetrics],
    by_slug: dict[str, CityMetrics],
    inputs: DecisionInputs,
) -> list[CityMetrics]:
    if inputs.candidate_city_slugs is None:
        return [city for city in metrics if city.slug != inputs.baseline_city_slug]

    requested_slugs = list(dict.fromkeys(inputs.candidate_city_slugs))
    if inputs.baseline_city_slug in requested_slugs:
        raise ValueError(
            f"Baseline city cannot also be a candidate: {inputs.baseline_city_slug}"
        )

    missing = [slug for slug in requested_slugs if slug not in by_slug]
    if missing:
        raise ValueError(f"Candidate cities not found: {', '.join(missing)}")

    return [by_slug[slug] for slug in requested_slugs]


def _as_metrics(city: CityMetrics | CityDetail) -> CityMetrics:
    if isinstance(city, CityDetail):
        return city.metrics
    return city


def _build_city_decision(
    city: CityMetrics,
    baseline: CityMetrics,
    inputs: DecisionInputs,
    *,
    dataset_count: int,
    as_of: date,
) -> RelocationDecision:
    constraints = _constraint_checks(city, baseline, inputs)
    flags = _skeptic_flags(city, inputs, dataset_count=dataset_count, as_of=as_of)
    verdict = _verdict(constraints, flags)

    return RelocationDecision(
        city_slug=city.slug,
        city_name=city.name,
        state_code=city.state_code,
        verdict=verdict,
        constraints=constraints,
        skeptic_flags=flags,
        evidence=_decision_evidence(city, inputs),
    )


def _constraint_checks(
    city: CityMetrics,
    baseline: CityMetrics,
    inputs: DecisionInputs,
) -> list[ConstraintCheck]:
    checks = [
        ConstraintCheck(
            key="max_rent",
            label="Rent target",
            passed=city.median_rent <= inputs.max_rent,
            evidence=(
                f"${city.median_rent:,.0f} median rent vs "
                f"${inputs.max_rent:,.0f} max rent"
            ),
        ),
        ConstraintCheck(
            key="offer_rent_burden",
            label="Rent burden on offer",
            passed=_rent_burden(city, inputs.offer_salary) <= 0.30,
            evidence=(
                f"{_rent_burden(city, inputs.offer_salary):.0%} of "
                f"${inputs.offer_salary:,.0f} offer salary"
            ),
        ),
    ]

    if inputs.require_warmer_than_baseline:
        checks.append(_warmer_check(city, baseline))
    if inputs.require_civic_fit:
        checks.append(
            ConstraintCheck(
                key="civic_fit",
                label="Civic fit",
                passed=False,
                evidence="No civic-participation decision data is available yet.",
            )
        )
    if inputs.require_downtown_fit:
        checks.append(
            ConstraintCheck(
                key="downtown_fit",
                label="Downtown fit",
                passed=False,
                evidence="No downtown-fit decision data is available yet.",
            )
        )

    return checks


def _warmer_check(city: CityMetrics, baseline: CityMetrics) -> ConstraintCheck:
    if city.avg_temp_f is None or baseline.avg_temp_f is None:
        return ConstraintCheck(
            key="warmer_than_baseline",
            label="Warmer than baseline",
            passed=False,
            evidence="Average temperature is missing for candidate or baseline.",
        )

    return ConstraintCheck(
        key="warmer_than_baseline",
        label="Warmer than baseline",
        passed=city.avg_temp_f > baseline.avg_temp_f,
        evidence=(
            f"{city.avg_temp_f:.1f}F candidate average vs "
            f"{baseline.avg_temp_f:.1f}F baseline average"
        ),
    )


def _skeptic_flags(
    city: CityMetrics,
    inputs: DecisionInputs,
    *,
    dataset_count: int,
    as_of: date,
) -> list[SkepticFlag]:
    flags: list[SkepticFlag] = []

    if dataset_count < inputs.limited_dataset_threshold:
        flags.append(
            SkepticFlag(
                key="limited_dataset",
                label="Limited dataset",
                evidence=(
                    f"Decision run has {dataset_count} cities; "
                    f"threshold is {inputs.limited_dataset_threshold}."
                ),
            )
        )

    trusts = {
        "affordability": city.affordability_trust,
        "job_market": city.job_market_trust,
        "safety": city.safety_trust,
        "climate": city.climate_trust,
        "social": city.social_trust,
    }
    for dimension, trust in trusts.items():
        flags.extend(_trust_flags(dimension, trust, inputs, as_of))

    if city.median_home_price_is_imputed:
        flags.append(
            SkepticFlag(
                key="proxy_median_home_price",
                label="Proxy home price",
                evidence=(
                    f"Median home price is imputed from {city.median_home_price_source} "
                    f"({city.median_home_price_source_date})."
                ),
            )
        )
    if city.job_growth_is_imputed:
        flags.append(
            SkepticFlag(
                key="proxy_job_growth",
                label="Proxy job growth",
                evidence=(
                    f"Job growth is imputed from {city.job_growth_source} "
                    f"({city.job_growth_source_date})."
                ),
            )
        )

    for key, label, source_date in (
        ("median_home_price_date", "Home price source date", city.median_home_price_source_date),
        ("job_growth_date", "Job growth source date", city.job_growth_source_date),
    ):
        date_flag = _source_date_flag(key, label, source_date, inputs, as_of)
        if date_flag is not None:
            flags.append(date_flag)

    return flags


def _trust_flags(
    dimension: str,
    trust: DimensionTrust,
    inputs: DecisionInputs,
    as_of: date,
) -> list[SkepticFlag]:
    flags: list[SkepticFlag] = []
    label = dimension.replace("_", " ").title()

    if trust.confidence == "seeded":
        flags.append(
            SkepticFlag(
                key=f"seeded_{dimension}",
                label=f"Seeded {label.lower()}",
                evidence=f"{label} uses seeded context from {trust.source}.",
            )
        )
    elif trust.confidence in {"estimated", "missing"} or trust.is_imputed:
        flags.append(
            SkepticFlag(
                key=f"proxy_{dimension}",
                label=f"Proxy {label.lower()}",
                evidence=(
                    f"{label} confidence is {trust.confidence}; "
                    f"source is {trust.source}."
                ),
            )
        )

    date_flag = _source_date_flag(
        f"{dimension}_source_date",
        f"{label} source date",
        trust.source_date,
        inputs,
        as_of,
    )
    if date_flag is not None:
        flags.append(date_flag)

    return flags


def _source_date_flag(
    key: str,
    label: str,
    source_date: str,
    inputs: DecisionInputs,
    as_of: date,
) -> SkepticFlag | None:
    parsed = _parse_source_date(source_date)
    if parsed is None:
        return SkepticFlag(
            key=f"unknown_{key}",
            label=f"Unknown {label.lower()}",
            evidence=f"{label} is {source_date!r}.",
        )

    age_days = (as_of - parsed).days
    if age_days > inputs.stale_after_days:
        return SkepticFlag(
            key=f"stale_{key}",
            label=f"Stale {label.lower()}",
            evidence=(
                f"{label} is {source_date}; "
                f"{age_days} days old as of {as_of.isoformat()}."
            ),
        )
    return None


def _parse_source_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"unknown", "n/a", "na", "tbd"}:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
        return parsed.date()
    return None


def _verdict(constraints: list[ConstraintCheck], flags: list[SkepticFlag]) -> Verdict:
    if any(not check.passed for check in constraints):
        return "Keep looking"
    if flags:
        return "Viable but risky"
    return "Take it"


def _decision_evidence(city: CityMetrics, inputs: DecisionInputs) -> list[str]:
    return [
        f"${city.median_rent:,.0f} median rent",
        f"{_rent_burden(city, inputs.offer_salary):.0%} rent burden on offer",
        f"{city.unemployment_pct:.1f}% unemployment",
        f"{city.safety_score_raw / 10:.1f}/10 safety signal",
        f"{city.climate_score_raw / 10:.1f}/10 climate signal",
    ]


def _rent_burden(city: CityMetrics, offer_salary: float) -> float:
    return (city.median_rent * 12) / offer_salary
