"""Deterministic questionnaire traversal and validation."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .models import Intent, OnboardingState, QUESTIONNAIRE_VERSION, SalaryInput
from .questions import QUESTION_BY_ID, QUESTIONS, QuestionDefinition, QuestionKind


class OnboardingValidationError(ValueError):
    pass


def normalize_state(state: OnboardingState) -> OnboardingState:
    """Apply explicit skip semantics without guessing any other answer."""
    if state.version != QUESTIONNAIRE_VERSION:
        raise OnboardingValidationError(f"unsupported questionnaire version: {state.version}")
    if "intent" in state.skipped:
        return state.model_copy(
            update={
                "answers": {**state.answers, "intent": Intent.EXPLORE.value},
                "skipped": state.skipped - {"intent"},
            }
        )
    return state


def validate_answer(question_id: str, value: Any) -> Any:
    try:
        question = QUESTION_BY_ID[question_id]
    except KeyError as exc:
        raise OnboardingValidationError(f"unknown question: {question_id}") from exc

    if question.kind is QuestionKind.SINGLE_SELECT:
        normalized = value.value if hasattr(value, "value") else value
        if normalized not in question.options:
            raise OnboardingValidationError(
                f"invalid answer for {question_id}; expected one of {question.options}"
            )
        return normalized
    if question.kind is QuestionKind.TEXT:
        if not isinstance(value, str) or not value.strip():
            raise OnboardingValidationError(f"{question_id} must be non-empty text")
        return value.strip()
    if question.kind is QuestionKind.SALARY:
        try:
            return value if isinstance(value, SalaryInput) else SalaryInput.model_validate(value)
        except ValidationError as exc:
            raise OnboardingValidationError(str(exc)) from exc
    raise OnboardingValidationError(f"unsupported question kind: {question.kind}")


def validate_state(state: OnboardingState) -> OnboardingState:
    state = normalize_state(state)
    unknown = (set(state.answers) | state.skipped) - set(QUESTION_BY_ID)
    if unknown:
        raise OnboardingValidationError(f"unknown questions: {sorted(unknown)}")

    validated: dict[str, Any] = {}
    for question_id, value in state.answers.items():
        validated[question_id] = validate_answer(question_id, value)

    for question_id in state.skipped:
        question = QUESTION_BY_ID[question_id]
        if not question.skippable:
            raise OnboardingValidationError(f"question cannot be skipped: {question_id}")

    for question_id in set(validated) | state.skipped:
        question = QUESTION_BY_ID[question_id]
        if not question.applies(validated):
            raise OnboardingValidationError(f"question does not apply to this path: {question_id}")

    return state.model_copy(update={"answers": validated})


def next_question(state: OnboardingState) -> QuestionDefinition | None:
    state = validate_state(state)
    completed = set(state.answers) | state.skipped
    for question in QUESTIONS:
        if question.id not in completed and question.applies(state.answers):
            return question
    return None


def is_complete(state: OnboardingState) -> bool:
    return next_question(state) is None
