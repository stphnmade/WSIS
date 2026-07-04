from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from wsis.data.ingestion.common import load_raw_csv, normalize_city_name
from wsis.data.ingestion.github_jobs import GITHUB_API_URL, _headers


REQUIRED_CANONICAL_COLUMNS = {
    "city", "state_id", "state_name", "county_fips", "county_name", "lat", "lng", "population"
}


def fetch_github_geography(
    canonical_path: Path,
    repository: str,
    cities_path: str,
    token: str = "",
    timeout: float = 30,
) -> pd.DataFrame:
    """Refresh canonical cities from GitHub while retaining county-FIPS join keys."""
    canonical = load_raw_csv(canonical_path, dtype={"county_fips": str})
    missing = REQUIRED_CANONICAL_COLUMNS.difference(canonical.columns)
    if missing:
        raise ValueError(f"Canonical city file is missing columns: {sorted(missing)}")

    metadata = requests.get(
        GITHUB_API_URL.format(repository=repository, path=cities_path),
        headers=_headers(token),
        timeout=timeout,
    )
    metadata.raise_for_status()
    download_url = metadata.json().get("download_url")
    if not download_url:
        raise ValueError("GitHub contents response did not include download_url")
    response = requests.get(download_url, headers=_headers(token), timeout=timeout)
    response.raise_for_status()

    lookup = {
        (normalize_city_name(str(item["name"])), str(item["state_code"]).upper()): item
        for item in response.json()
        if item.get("name") and item.get("state_code")
    }
    rows = []
    unmatched = []
    for row in canonical.itertuples(index=False):
        key = (normalize_city_name(str(row.city)), str(row.state_id).upper())
        source = lookup.get(key)
        if source is None:
            unmatched.append(f"{row.city}, {row.state_id}")
            continue
        rows.append({
            "city": row.city,
            "state_id": row.state_id,
            "state_name": row.state_name,
            "county_fips": str(row.county_fips).zfill(5),
            "county_name": row.county_name,
            "lat": float(source["latitude"]),
            "lng": float(source["longitude"]),
            "population": int(source.get("population") or row.population),
            "timezone": source.get("timezone") or "",
            "github_city_id": source.get("id"),
            "github_updated_at": source.get("updated_at") or "",
            "geography_source": f"github:{repository}/{cities_path}",
        })
    if unmatched:
        raise ValueError(f"GitHub geography did not match canonical cities: {', '.join(unmatched)}")
    result = pd.DataFrame(rows)
    if len(result) != len(canonical) or result[["city", "state_id"]].duplicated().any():
        raise ValueError("GitHub geography refresh did not preserve one row per canonical city")
    return result
