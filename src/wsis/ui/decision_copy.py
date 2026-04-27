from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from wsis.decision import DecisionInputs, RelocationDecision, build_relocation_decisions
from wsis.domain.models import CityDetail


VerdictKind = Literal["take", "risky", "keep_looking"]
EvidenceFlag = Literal["weak", "missing", "seeded", "proxy"]


@dataclass(frozen=True)
class CheckResult:
    label: str
    status: Literal["pass", "fail", "review"]
    value: str
    detail: str


@dataclass(frozen=True)
class EvidenceIssue:
    flag: EvidenceFlag
    title: str
    detail: str


@dataclass(frozen=True)
class DecisionSummary:
    verdict: VerdictKind
    headline: str
    subhead: str
    checks: tuple[CheckResult, ...]
    evidence_issues: tuple[EvidenceIssue, ...]
    pass_actions: tuple[str, ...]
    proof_points: tuple[str, ...]
    no_rent_match: bool


def money(value: float) -> str:
    return f"${value:,.0f}"


def signed_money(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.0f}%"


def city_label(detail: CityDetail) -> str:
    return f"{detail.summary.name}, {detail.summary.state_code}"


def rent_share_of_salary(monthly_rent: float, annual_salary: float) -> float | None:
    if annual_salary <= 0:
        return None
    return monthly_rent * 12 / annual_salary


def salary_fit_label(monthly_rent: float, annual_salary: float) -> str:
    share = rent_share_of_salary(monthly_rent, annual_salary)
    if share is None:
        return "No salary"
    return f"{pct(share * 100)} of gross pay"


def verdict_copy(verdict: VerdictKind, candidate: CityDetail) -> tuple[str, str]:
    label = city_label(candidate)
    if verdict == "take":
        return (
            f"David can take {label} to verification.",
            "Hard checks pass; Sarah still reviews the evidence quality below.",
        )
    if verdict == "risky":
        return (
            f"{label} is viable but risky.",
            "David's constraints pass, but Sarah found evidence concerns.",
        )
    return (
        f"Keep looking before committing to {label}.",
        "At least one hard constraint fails.",
    )


def verdict_kind(verdict: str) -> VerdictKind:
    if verdict == "Take it":
        return "take"
    if verdict == "Viable but risky":
        return "risky"
    return "keep_looking"


def check_from_constraint(key: str, label: str, passed: bool, evidence: str) -> CheckResult:
    value, _, detail = evidence.partition(" vs ")
    if key == "offer_rent_burden":
        value = evidence.replace(" offer salary", "")
        detail = "Target is 30% or less."
    elif key in {"civic_fit", "downtown_fit"}:
        value = "Not wired yet"
        detail = evidence
    elif not detail:
        detail = evidence
    return CheckResult(
        label=label,
        status="pass" if passed else "fail",
        value=value,
        detail=detail,
    )


def evidence_flag_from_key(key: str) -> EvidenceFlag:
    if key.startswith("seeded_"):
        return "seeded"
    if key.startswith("unknown_"):
        return "missing"
    if key.startswith("proxy_") or key.startswith("stale_"):
        return "weak"
    return "proxy"


def evidence_issues(decision: RelocationDecision) -> tuple[EvidenceIssue, ...]:
    issues = [
        EvidenceIssue(
            flag=evidence_flag_from_key(flag.key),
            title=flag.label,
            detail=flag.evidence,
        )
        for flag in decision.skeptic_flags
    ]

    deduped: dict[tuple[EvidenceFlag, str], EvidenceIssue] = {}
    for issue in issues:
        deduped.setdefault((issue.flag, issue.title), issue)
    return tuple(deduped.values())


def pass_actions_for(
    checks: tuple[CheckResult, ...],
    issues: tuple[EvidenceIssue, ...],
    candidate: CityDetail,
    offer_salary: float,
    max_rent: float,
    no_rent_match: bool,
) -> tuple[str, ...]:
    actions: list[str] = []
    failed_checks = {check.label: check for check in checks if check.status == "fail"}

    if "Rent target" in failed_checks:
        rent_gap = candidate.metrics.median_rent - max_rent
        actions.append(
            f"Raise the rent ceiling by about {money(rent_gap)} or pick a city below {money(max_rent)}."
        )
    if "Rent burden on offer" in failed_checks:
        required_salary = (candidate.metrics.median_rent * 12) / 0.30
        if rent_share_of_salary(candidate.metrics.median_rent, offer_salary) is not None:
            actions.append(
                f"Verify an offer near {money(required_salary)} or better to keep rent under 30% of pay."
            )
    if "Warmer than baseline" in failed_checks:
        actions.append("Turn off the warmer-than-baseline constraint or choose a warmer candidate city.")
    if "Civic fit" in failed_checks:
        actions.append("Add a sourced civic-fit signal before requiring civic fit as a hard constraint.")
    if "Downtown fit" in failed_checks:
        actions.append("Add commute/downtown access data before requiring downtown fit as a hard constraint.")
    if no_rent_match and "Rent target" not in failed_checks:
        actions.append("Relax the rent ceiling; no non-baseline city currently meets it.")

    if not actions and issues:
        actions.append("Replace seeded or proxy evidence with source-backed data before treating this as a clean yes.")
    if not actions:
        actions.append("Hard checks pass; next step is outside validation of offer details and neighborhood fit.")

    return tuple(dict.fromkeys(actions[:4]))


def rent_match_count(
    details: Iterable[CityDetail],
    max_rent: float,
    baseline_slug: str | None = None,
) -> int:
    return sum(
        1
        for detail in details
        if detail.summary.slug != baseline_slug and detail.metrics.median_rent <= max_rent
    )


def build_decision_summary(
    candidate: CityDetail,
    baseline: CityDetail,
    all_details: Iterable[CityDetail],
    offer_salary: float,
    max_rent: float,
    require_warmer: bool,
    require_civic_fit: bool = False,
    require_downtown_fit: bool = False,
) -> DecisionSummary:
    details = list(all_details)
    inputs = DecisionInputs(
        baseline_city_slug=baseline.summary.slug,
        offer_salary=offer_salary,
        max_rent=max_rent,
        require_warmer_than_baseline=require_warmer,
        require_civic_fit=require_civic_fit,
        require_downtown_fit=require_downtown_fit,
    )
    run = build_relocation_decisions(details, inputs, dataset_count=len(details))
    decision = next(item for item in run.decisions if item.city_slug == candidate.summary.slug)
    checks = tuple(
        check_from_constraint(check.key, check.label, check.passed, check.evidence)
        for check in decision.constraints
    )
    issues = evidence_issues(decision)
    verdict = verdict_kind(decision.verdict)
    headline, subhead = verdict_copy(verdict, candidate)
    no_rent_match = rent_match_count(details, max_rent, baseline.summary.slug) == 0
    return DecisionSummary(
        verdict=verdict,
        headline=headline,
        subhead=subhead,
        checks=checks,
        evidence_issues=issues,
        pass_actions=pass_actions_for(checks, issues, candidate, offer_salary, max_rent, no_rent_match),
        proof_points=tuple(decision.evidence),
        no_rent_match=no_rent_match,
    )
