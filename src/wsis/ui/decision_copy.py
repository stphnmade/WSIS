from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from wsis.domain.models import CityDetail


VerdictKind = Literal["take", "risky", "keep_looking"]
EvidenceFlag = Literal["weak", "missing", "seeded", "proxy"]


@dataclass(frozen=True)
class DecisionInput:
    baseline_city: str
    candidate_city: str
    offer_salary: float
    max_rent: float
    require_warmer: bool


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


def warmer_status(candidate: CityDetail, baseline: CityDetail, required: bool) -> CheckResult:
    candidate_temp = candidate.metrics.avg_temp_f
    baseline_temp = baseline.metrics.avg_temp_f
    if candidate_temp is None or baseline_temp is None:
        return CheckResult(
            label="Warmer than baseline",
            status="review",
            value="Missing climate input",
            detail="Average temperature is unavailable for one city.",
        )

    delta = candidate_temp - baseline_temp
    status = "pass" if delta > 0 or not required else "fail"
    value = f"{candidate_temp:.0f}F vs {baseline_temp:.0f}F"
    detail = f"{delta:+.0f}F from {baseline.summary.name}"
    return CheckResult("Warmer than baseline", status, value, detail)


def core_checks(
    candidate: CityDetail,
    baseline: CityDetail,
    offer_salary: float,
    max_rent: float,
    require_warmer: bool,
) -> tuple[CheckResult, ...]:
    candidate_rent = candidate.metrics.median_rent
    rent_status = "pass" if candidate_rent <= max_rent else "fail"

    salary_share = rent_share_of_salary(candidate_rent, offer_salary)
    salary_status = "review"
    if salary_share is not None:
        salary_status = "pass" if salary_share <= 0.30 else "fail"

    return (
        CheckResult(
            label="Rent ceiling",
            status=rent_status,
            value=f"{money(candidate_rent)} / mo",
            detail=f"Target is {money(max_rent)}.",
        ),
        CheckResult(
            label="Salary fit",
            status=salary_status,
            value=salary_fit_label(candidate_rent, offer_salary),
            detail="Uses offered salary and median rent.",
        ),
        warmer_status(candidate, baseline, require_warmer),
    )


def verdict_from_checks(checks: Iterable[CheckResult]) -> VerdictKind:
    check_list = list(checks)
    if any(check.label == "Rent ceiling" and check.status == "fail" for check in check_list):
        return "keep_looking"
    if any(check.status == "fail" for check in check_list):
        return "risky"
    if any(check.status == "review" for check in check_list):
        return "risky"
    return "take"


def verdict_copy(verdict: VerdictKind, candidate: CityDetail) -> tuple[str, str]:
    label = city_label(candidate)
    if verdict == "take":
        return (
            f"{label} is viable on the current hard checks.",
            "Treat this as a candidate to verify, not a final recommendation.",
        )
    if verdict == "risky":
        return (
            f"{label} is possible, but not clean enough yet.",
            "Review the failed or uncertain checks before treating the offer as safe.",
        )
    return (
        f"Keep looking before committing to {label}.",
        "The current data does not support taking this offer.",
    )


def evidence_issues(candidate: CityDetail) -> tuple[EvidenceIssue, ...]:
    issues: list[EvidenceIssue] = [
        EvidenceIssue(
            flag="missing",
            title="Civic-fit proxy",
            detail="No independent civic-fit field is wired into this page yet.",
        ),
        EvidenceIssue(
            flag="missing",
            title="Downtown-vibe proxy",
            detail="No amenity, transit, or core-density score is available yet.",
        ),
    ]

    if candidate.reddit_panel.confidence == "seeded" or "seed" in candidate.reddit_panel.source.lower():
        issues.append(
            EvidenceIssue(
                flag="seeded",
                title="Review context",
                detail="Reddit-style context is seeded beta material and stays out of the verdict.",
            )
        )

    for dimension in candidate.summary.score_dimensions:
        source = dimension.source.lower()
        if dimension.confidence == "missing":
            issues.append(
                EvidenceIssue("missing", dimension.label, "This dimension has no usable source.")
            )
        elif dimension.confidence == "estimated" or dimension.is_imputed:
            issues.append(
                EvidenceIssue("weak", dimension.label, "This dimension uses estimated input.")
            )
        elif "sample" in source or "placeholder" in source:
            issues.append(
                EvidenceIssue("proxy", dimension.label, f"Source is currently {dimension.source}.")
            )
        elif not dimension.included_in_score:
            issues.append(
                EvidenceIssue("proxy", dimension.label, "Visible as context, not ranked evidence.")
            )

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
) -> DecisionSummary:
    checks = core_checks(candidate, baseline, offer_salary, max_rent, require_warmer)
    verdict = verdict_from_checks(checks)
    headline, subhead = verdict_copy(verdict, candidate)
    no_rent_match = rent_match_count(all_details, max_rent) == 0
    return DecisionSummary(
        verdict=verdict,
        headline=headline,
        subhead=subhead,
        checks=checks,
        evidence_issues=evidence_issues(candidate),
        no_rent_match=no_rent_match,
    )
