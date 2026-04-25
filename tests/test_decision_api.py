from fastapi.testclient import TestClient

from wsis.api.main import app


client = TestClient(app)


def test_decision_endpoint_runs_david_defaults_against_all_candidates() -> None:
    response = client.post(
        "/api/v1/decisions",
        json={
            "baseline_city_slug": "chicago-il",
            "offer_salary": 70000,
            "max_rent": 980,
            "require_warmer_than_baseline": True,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["baseline_city_slug"] == "chicago-il"
    assert payload["baseline_city_name"] == "Chicago"
    assert payload["candidate_count"] >= 1
    assert all(decision["city_slug"] != "chicago-il" for decision in payload["decisions"])
    assert all(
        decision["verdict"] != "Take it"
        for decision in payload["decisions"]
        if not next(
            check
            for check in decision["constraints"]
            if check["key"] == "max_rent"
        )["passed"]
    )


def test_decision_endpoint_accepts_explicit_candidate_slugs() -> None:
    response = client.post(
        "/api/v1/decisions",
        json={
            "baseline_city_slug": "chicago-il",
            "candidate_city_slugs": ["tampa-fl", "austin-tx"],
            "offer_salary": 70000,
            "max_rent": 980,
            "require_warmer_than_baseline": True,
            "require_civic_fit": False,
            "require_downtown_fit": False,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["candidate_count"] == 2
    assert [decision["city_slug"] for decision in payload["decisions"]] == [
        "tampa-fl",
        "austin-tx",
    ]


def test_decision_endpoint_returns_clear_error_for_missing_baseline() -> None:
    response = client.post(
        "/api/v1/decisions",
        json={
            "baseline_city_slug": "missing-city",
            "candidate_city_slugs": ["tampa-fl"],
            "offer_salary": 70000,
            "max_rent": 980,
            "require_warmer_than_baseline": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Baseline city not found: missing-city"


def test_decision_endpoint_returns_clear_error_for_missing_candidate() -> None:
    response = client.post(
        "/api/v1/decisions",
        json={
            "baseline_city_slug": "chicago-il",
            "candidate_city_slugs": ["missing-city"],
            "offer_salary": 70000,
            "max_rent": 980,
            "require_warmer_than_baseline": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate cities not found: missing-city"
