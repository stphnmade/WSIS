from fastapi.testclient import TestClient

from wsis.api.main import app


client = TestClient(app)


def test_public_auth_config_fails_closed_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("WSIS_SUPABASE_URL", raising=False)
    monkeypatch.delenv("WSIS_SUPABASE_PUBLISHABLE_KEY", raising=False)

    response = client.get("/api/auth/config")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "supabase_url": "",
        "publishable_key": "",
    }


def test_me_requires_bearer_token() -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
