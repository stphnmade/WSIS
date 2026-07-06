from fastapi.testclient import TestClient

from wsis.api.main import app


client = TestClient(app)


def test_explore_returns_real_job_covered_places() -> None:
    response = client.get("/api/v1/explore", params={"limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert all(item["place_geoid"] and item["active_listing_count"] > 0 for item in payload)


def test_jobs_returns_listing_level_data() -> None:
    places = client.get("/api/v1/explore", params={"limit": 1}).json()
    response = client.get("/api/v1/jobs", params={"place_geoid": places[0]["place_geoid"], "limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["company_name"]
    assert payload[0]["job_url"].startswith("http")


def test_explore_can_rank_places_by_requested_role() -> None:
    response = client.get("/api/v1/explore", params={"limit": 10, "role": "software engineer"})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload == sorted(payload, key=lambda item: item["active_listing_count"], reverse=True)
