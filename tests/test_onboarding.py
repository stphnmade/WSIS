import pytest
from pydantic import ValidationError

from wsis.onboarding import (
    OfferResultSpec,
    OnboardingState,
    OnboardingValidationError,
    SalaryInput,
    is_complete,
    next_question,
    normalize_state,
    validate_state,
)


def test_first_question_is_intent_and_skip_becomes_explore():
    assert next_question(OnboardingState()).id == "intent"
    state = normalize_state(OnboardingState(skipped={"intent"}))
    assert state.answers["intent"] == "explore"
    assert "intent" not in state.skipped
    assert next_question(state).id == "social_access"


def test_offer_path_is_deterministic():
    state = OnboardingState(answers={"intent": "offer"})
    assert next_question(state).id == "offered_city"
    state.answers["offered_city"] = "Atlanta, GA"
    assert next_question(state).id == "salary"


def test_opportunity_path_requires_roles_and_never_asks_offer_fields():
    state = OnboardingState(answers={"intent": "opportunities"})
    assert next_question(state).id == "roles"
    state.answers["roles"] = "data engineering"
    seen = []
    while (question := next_question(state)) is not None:
        seen.append(question.id)
        state.skipped.add(question.id)
    assert "offered_city" not in seen
    assert "salary" not in seen


def test_small_place_triggers_metro_followup_only_for_small_place():
    base = {
        "intent": "explore",
        "social_access": "some",
        "crowd_level": "mix",
    }
    small = OnboardingState(answers={**base, "place_scale": "small_place"})
    assert next_question(small).id == "small_place_metro"

    major = OnboardingState(answers={**base, "place_scale": "major_city"})
    assert next_question(major).id == "greenery_type"


def test_branch_answer_is_rejected_when_branch_does_not_apply():
    state = OnboardingState(
        answers={
            "intent": "explore",
            "place_scale": "major_city",
            "small_place_metro": "either",
        }
    )
    with pytest.raises(OnboardingValidationError, match="does not apply"):
        validate_state(state)


def test_non_skippable_branch_questions_are_enforced():
    with pytest.raises(OnboardingValidationError, match="cannot be skipped"):
        validate_state(OnboardingState(answers={"intent": "offer"}, skipped={"offered_city"}))
    with pytest.raises(OnboardingValidationError, match="cannot be skipped"):
        validate_state(OnboardingState(answers={"intent": "opportunities"}, skipped={"roles"}))


def test_salary_exact_value_is_not_persistable_without_consent():
    salary = SalaryInput(band="90k_130k", exact_annual_usd=112_500)
    assert salary.persistable_exact_value is None

    saved = SalaryInput(
        band="90k_130k",
        exact_annual_usd=112_500,
        save_exact_consent=True,
        consent_version="salary-save.v1",
    )
    assert saved.persistable_exact_value == 112_500


def test_salary_save_consent_is_explicit_and_versioned():
    with pytest.raises(ValidationError, match="consent_version"):
        SalaryInput(band="60k_90k", exact_annual_usd=80_000, save_exact_consent=True)
    with pytest.raises(ValidationError, match="requires exact_annual_usd"):
        SalaryInput(band="60k_90k", save_exact_consent=True, consent_version="v1")


def test_civic_context_is_comparison_only():
    state = OnboardingState(
        answers={
            "intent": "explore",
            "social_access": "some",
            "crowd_level": "mix",
            "place_scale": "open",
            "greenery_type": "both",
            "civic_context": "context_only",
        }
    )
    assert is_complete(state)

    with pytest.raises(OnboardingValidationError, match="invalid answer"):
        validate_state(state.model_copy(update={"answers": {**state.answers, "civic_context": "rank_me"}}))


def test_offer_result_is_offer_plus_exactly_four_unique_alternatives():
    result = OfferResultSpec(
        offered_place_geoid="1304000",
        alternative_place_geoids=("1245000", "3712000", "4805000", "0667000"),
    )
    assert len(result.alternative_place_geoids) == 4

    with pytest.raises(ValidationError, match="must be unique"):
        OfferResultSpec(
            offered_place_geoid="1304000",
            alternative_place_geoids=("1304000", "3712000", "4805000", "0667000"),
        )


def test_unknown_questions_and_questionnaire_versions_are_rejected():
    with pytest.raises(OnboardingValidationError, match="unknown questions"):
        validate_state(OnboardingState(answers={"intent": "explore", "personality": "introvert"}))
    with pytest.raises(OnboardingValidationError, match="unsupported questionnaire version"):
        validate_state(OnboardingState(version="old", answers={"intent": "explore"}))
