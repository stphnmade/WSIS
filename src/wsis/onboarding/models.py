"""Typed inputs for the deterministic WSIS onboarding flow."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


QUESTIONNAIRE_VERSION = "2026-07-05.v1"


class Intent(str, Enum):
    OFFER = "offer"
    OPPORTUNITIES = "opportunities"
    EXPLORE = "explore"


class SocialAccess(str, Enum):
    LOW = "low"
    SOME = "some"
    A_LOT = "a_lot"
    NOT_SURE = "not_sure"


class CrowdLevel(str, Enum):
    QUIET = "quiet"
    MIX = "mix"
    LIVELY = "lively"
    NO_PREFERENCE = "no_preference"


class PlaceScale(str, Enum):
    MAJOR_CITY = "major_city"
    MIDSIZE_CITY = "midsize_city"
    SMALL_PLACE = "small_place"
    OPEN = "open"


class SmallPlaceMetroPreference(str, Enum):
    WITHIN_MAJOR_METRO = "within_major_metro"
    OUTSIDE_MAJOR_METRO = "outside_major_metro"
    EITHER = "either"


class GreeneryType(str, Enum):
    EVERYDAY_GREEN = "everyday_green"
    WEEKEND_NATURE = "weekend_nature"
    BOTH = "both"
    NO_PREFERENCE = "no_preference"


class CivicContext(str, Enum):
    OMIT = "omit"
    CONTEXT_ONLY = "context_only"


class SalaryBand(str, Enum):
    UNDER_40K = "under_40k"
    FROM_40K_TO_60K = "40k_60k"
    FROM_60K_TO_90K = "60k_90k"
    FROM_90K_TO_130K = "90k_130k"
    FROM_130K_TO_180K = "130k_180k"
    OVER_180K = "over_180k"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class SalaryInput(BaseModel):
    """Salary is banded unless separate exact-value storage consent is given."""

    band: SalaryBand
    exact_annual_usd: int | None = Field(default=None, ge=1, le=10_000_000)
    save_exact_consent: bool = False
    consent_version: str | None = None

    @model_validator(mode="after")
    def validate_exact_consent(self) -> "SalaryInput":
        if self.save_exact_consent and self.exact_annual_usd is None:
            raise ValueError("save_exact_consent requires exact_annual_usd")
        if self.save_exact_consent and not self.consent_version:
            raise ValueError("saved exact salary requires a consent_version")
        if not self.save_exact_consent and self.consent_version is not None:
            raise ValueError("consent_version is only valid when exact salary is saved")
        return self

    @property
    def persistable_exact_value(self) -> int | None:
        return self.exact_annual_usd if self.save_exact_consent else None


class OnboardingState(BaseModel):
    version: str = QUESTIONNAIRE_VERSION
    answers: dict[str, Any] = Field(default_factory=dict)
    skipped: set[str] = Field(default_factory=set)

    @model_validator(mode="after")
    def no_answered_question_is_skipped(self) -> "OnboardingState":
        overlap = set(self.answers).intersection(self.skipped)
        if overlap:
            raise ValueError(f"questions cannot be answered and skipped: {sorted(overlap)}")
        return self


class OfferResultSpec(BaseModel):
    """Stable output contract: verdict on the offer, then four alternatives."""

    offered_place_geoid: str = Field(pattern=r"^\d{7}$")
    alternative_place_geoids: tuple[str, str, str, str]

    @model_validator(mode="after")
    def unique_places(self) -> "OfferResultSpec":
        all_places = (self.offered_place_geoid, *self.alternative_place_geoids)
        if len(set(all_places)) != 5:
            raise ValueError("offered city and four alternatives must be unique")
        if any(len(value) != 7 or not value.isdigit() for value in all_places):
            raise ValueError("all place GEOIDs must contain seven digits")
        return self
