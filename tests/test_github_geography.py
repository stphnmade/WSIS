from pathlib import Path

import pandas as pd

from wsis.data.ingestion.github_geography import fetch_github_geography


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_github_geography_preserves_county_fips(tmp_path: Path, monkeypatch) -> None:
    canonical = tmp_path / "cities.csv"
    pd.DataFrame([{
        "city": "Austin", "state_id": "TX", "state_name": "Texas",
        "county_fips": "48453", "county_name": "Travis", "lat": 0,
        "lng": 0, "population": 1,
    }]).to_csv(canonical, index=False)
    responses = iter([
        _Response({"download_url": "https://example.test/cities.json"}),
        _Response([{
            "id": 42, "name": "Austin", "state_code": "TX",
            "latitude": "30.26715", "longitude": "-97.74306",
            "population": 974447, "timezone": "America/Chicago",
            "updated_at": "2025-12-02T14:39:31",
        }]),
    ])
    monkeypatch.setattr("wsis.data.ingestion.github_geography.requests.get", lambda *args, **kwargs: next(responses))

    result = fetch_github_geography(canonical, "owner/repo", "cities.json")

    assert result.loc[0, "county_fips"] == "48453"
    assert result.loc[0, "population"] == 974447
    assert result.loc[0, "timezone"] == "America/Chicago"
    assert result.loc[0, "geography_source"] == "github:owner/repo/cities.json"
