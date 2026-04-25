from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal["Take it", "Viable but risky", "Keep looking"]
FlagSeverity = Literal["info", "warning"]


class DecisionInputs(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    baseline_city_slug: str = Field(min_length=1)
    offer_salary: float = Field(gt=0)
    max_rent: float = Field(gt=0)
    require_warmer_than_baseline: bool = False
    require_civic_fit: bool = False
    require_downtown_fit: bool = False
    stale_after_days: int = Field(default=730, gt=0)
    limited_dataset_threshold: int = Field(default=10, gt=0)


class ConstraintCheck(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    passed: bool
    evidence: str = Field(min_length=1)


class SkepticFlag(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    severity: FlagSeverity = "warning"
    evidence: str = Field(min_length=1)


class RelocationDecision(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    city_slug: str = Field(min_length=1)
    city_name: str = Field(min_length=1)
    state_code: str = Field(min_length=2, max_length=2)
    verdict: Verdict
    constraints: list[ConstraintCheck] = Field(default_factory=list)
    skeptic_flags: list[SkepticFlag] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class DecisionRun(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    baseline_city_slug: str = Field(min_length=1)
    baseline_city_name: str = Field(min_length=1)
    candidate_count: int = Field(ge=0)
    decisions: list[RelocationDecision] = Field(default_factory=list)
