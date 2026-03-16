from __future__ import annotations

from collections.abc import Mapping

from wsis.domain.models import ScoreWeights


WEIGHT_STATE_KEYS = {
    "affordability": "weight_affordability",
    "job_market": "weight_job_market",
    "safety": "weight_safety",
    "climate": "weight_climate",
    "social_sentiment": "weight_social_sentiment",
}


def default_score_weights() -> ScoreWeights:
    return ScoreWeights(
        affordability=40,
        job_market=25,
        safety=15,
        climate=10,
        social_sentiment=10,
    )


def score_weights_from_state(state: Mapping[str, object]) -> ScoreWeights:
    defaults = default_score_weights()
    return ScoreWeights(
        affordability=float(state.get(WEIGHT_STATE_KEYS["affordability"], defaults.affordability)),
        job_market=float(state.get(WEIGHT_STATE_KEYS["job_market"], defaults.job_market)),
        safety=float(state.get(WEIGHT_STATE_KEYS["safety"], defaults.safety)),
        climate=float(state.get(WEIGHT_STATE_KEYS["climate"], defaults.climate)),
        social_sentiment=float(
            state.get(WEIGHT_STATE_KEYS["social_sentiment"], defaults.social_sentiment)
        ),
    )
