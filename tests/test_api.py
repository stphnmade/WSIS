from fastapi.testclient import TestClient

from wsis.api.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_city_list_endpoint() -> None:
    response = client.get("/api/v1/cities")

    payload = response.json()
    assert response.status_code == 200
    assert len(payload) >= 5
    assert "slug" in payload[0]
    assert payload[0]["score_context"]["eligible_for_mvp_ranking"] is True
    assert "Social sentiment" in payload[0]["score_context"]["excluded_dimensions"]
    assert any(
        dimension["key"] == "social_sentiment" and dimension["included_in_score"] is False
        for dimension in payload[0]["score_dimensions"]
    )
    assert "exclusion_reasons" in payload[0]["score_context"]


def test_compare_endpoint_requires_two_cities() -> None:
    response = client.get("/api/v1/compare", params=[("slugs", "austin-tx")])

    assert response.status_code == 422


def test_city_detail_includes_reddit_freshness_and_provenance() -> None:
    response = client.get("/api/v1/cities/austin-tx")

    payload = response.json()
    assert response.status_code == 200
    assert payload["reddit_panel"]["generated_at"]
    assert payload["reddit_panel"]["posts_analyzed"] > 0
    assert payload["reddit_panel"]["provenance"]
    assert payload["reddit_panel"]["source"] == "precomputed_city_sentiment"
    assert payload["reddit_panel"]["included_in_score"] is False
    assert payload["summary"]["score_context"]["overall_confidence"] == "source_backed"
    assert payload["metrics"]["median_home_price_source"]
    assert payload["metrics"]["job_growth_source"]
