"""Versioned onboarding questions and declarative branch rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import (
    CivicContext,
    CrowdLevel,
    GreeneryType,
    Intent,
    PlaceScale,
    QUESTIONNAIRE_VERSION,
    SmallPlaceMetroPreference,
    SocialAccess,
)


class QuestionKind(str, Enum):
    SINGLE_SELECT = "single_select"
    TEXT = "text"
    SALARY = "salary"


@dataclass(frozen=True)
class BranchRule:
    question_id: str
    equals: Any

    def matches(self, answers: dict[str, Any]) -> bool:
        value = answers.get(self.question_id)
        return value == self.equals or value == getattr(self.equals, "value", object())


@dataclass(frozen=True)
class QuestionDefinition:
    id: str
    prompt: str
    why: str
    kind: QuestionKind
    options: tuple[str, ...] = ()
    branches: tuple[BranchRule, ...] = ()
    skippable: bool = True
    sensitive: bool = False

    def applies(self, answers: dict[str, Any]) -> bool:
        return all(rule.matches(answers) for rule in self.branches)


def _values(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(item.value for item in enum_type)


QUESTIONS_VERSION = QUESTIONNAIRE_VERSION
QUESTIONS: tuple[QuestionDefinition, ...] = (
    QuestionDefinition(
        "intent",
        "What would you like help deciding?",
        "This chooses the shortest relevant path. Skipping opens general exploration.",
        QuestionKind.SINGLE_SELECT,
        _values(Intent),
        skippable=True,
    ),
    QuestionDefinition(
        "offered_city",
        "Which city is the offer based in?",
        "The offer city anchors the verdict and comparison.",
        QuestionKind.TEXT,
        branches=(BranchRule("intent", Intent.OFFER),),
        skippable=False,
    ),
    QuestionDefinition(
        "salary",
        "What annual salary range does the offer provide?",
        "A range is enough to estimate affordability; exact values are optional.",
        QuestionKind.SALARY,
        branches=(BranchRule("intent", Intent.OFFER),),
        sensitive=True,
    ),
    QuestionDefinition(
        "roles",
        "What roles or skills should we match?",
        "We use this to find relevant work rather than count unrelated listings.",
        QuestionKind.TEXT,
        branches=(BranchRule("intent", Intent.OPPORTUNITIES),),
        skippable=False,
    ),
    QuestionDefinition(
        "social_access",
        "How much easy access to social activities do you want nearby?",
        "This measures access, not your personality.",
        QuestionKind.SINGLE_SELECT,
        _values(SocialAccess),
    ),
    QuestionDefinition(
        "crowd_level",
        "How do you feel about crowds and busy public spaces?",
        "Social access and tolerance for busy places are separate tradeoffs.",
        QuestionKind.SINGLE_SELECT,
        _values(CrowdLevel),
    ),
    QuestionDefinition(
        "place_scale",
        "What kind of place feels right?",
        "Population, density, and metro context affect daily life and job access.",
        QuestionKind.SINGLE_SELECT,
        _values(PlaceScale),
    ),
    QuestionDefinition(
        "small_place_metro",
        "Should a small place be within a major metro or outside one?",
        "A small suburb and an independent small town can have very different access.",
        QuestionKind.SINGLE_SELECT,
        _values(SmallPlaceMetroPreference),
        branches=(BranchRule("place_scale", PlaceScale.SMALL_PLACE),),
    ),
    QuestionDefinition(
        "greenery_type",
        "What kind of access to greenery matters?",
        "Everyday parks and weekend access to substantial nature are measured differently.",
        QuestionKind.SINGLE_SELECT,
        _values(GreeneryType),
    ),
    QuestionDefinition(
        "civic_context",
        "Would you like civic or political context included in comparisons?",
        "This is optional, comparison-only, and never inferred or used to exclude places.",
        QuestionKind.SINGLE_SELECT,
        _values(CivicContext),
        sensitive=True,
    ),
)

QUESTION_BY_ID = {question.id: question for question in QUESTIONS}
