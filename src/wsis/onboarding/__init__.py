"""Deterministic, privacy-conscious onboarding contracts."""

from .engine import (
    OnboardingValidationError,
    is_complete,
    next_question,
    normalize_state,
    validate_answer,
    validate_state,
)
from .models import Intent, OfferResultSpec, OnboardingState, SalaryInput
from .questions import QUESTIONS, QUESTIONS_VERSION, QuestionDefinition

__all__ = [
    "Intent",
    "OfferResultSpec",
    "OnboardingState",
    "OnboardingValidationError",
    "QUESTIONS",
    "QUESTIONS_VERSION",
    "QuestionDefinition",
    "SalaryInput",
    "is_complete",
    "next_question",
    "normalize_state",
    "validate_answer",
    "validate_state",
]
