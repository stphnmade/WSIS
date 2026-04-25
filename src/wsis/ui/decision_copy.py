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


def rent_match_count(details: Iterable[CityDetail], max_rent: float) -> int:
    return sum(1 for detail in details if detail.metrics.median_rent <= max_rent)


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
    verdict = verdict_kind(decision.verdict)
    headline, subhead = verdict_copy(verdict, candidate)
    no_rent_match = rent_match_count(details, max_rent) == 0
    return DecisionSummary(
        verdict=verdict,
        headline=headline,
        subhead=subhead,
        checks=checks,
        evidence_issues=evidence_issues(decision),
        proof_points=tuple(decision.evidence),
        no_rent_match=no_rent_match,
    )
