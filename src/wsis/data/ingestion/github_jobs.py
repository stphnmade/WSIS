from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

import pandas as pd
import requests

from wsis.data.ingestion.common import build_city_slug, load_raw_csv, normalize_city_name


GITHUB_API_URL = "https://api.github.com/repos/{repository}/contents/{path}"
LOCATION_PATTERN = re.compile(r"^\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s*$")


def _headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "WSIS-data-pipeline"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_github_jobs_data(
    cities_path: Path,
    repository: str,
    listings_path: str,
    token: str = "",
    timeout: float = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cities = load_raw_csv(cities_path, dtype={"county_fips": str})
    city_lookup = {
        (normalize_city_name(str(row.city)), str(row.state_id).upper()): row
        for row in cities.itertuples(index=False)
    }
    metadata = requests.get(
        GITHUB_API_URL.format(repository=repository, path=listings_path),
        headers=_headers(token), timeout=timeout,
    )
    metadata.raise_for_status()
    payload = metadata.json()
    download_url = payload.get("download_url")
    if not download_url:
        raise ValueError("GitHub contents response did not include download_url")
    response = requests.get(download_url, headers=_headers(token), timeout=timeout)
    response.raise_for_status()

    counts: dict[tuple[str, str], int] = {key: 0 for key in city_lookup}
    source_updated: dict[tuple[str, str], int] = {key: 0 for key in city_lookup}
    detail_rows = []
    for listing in response.json():
        if not listing.get("active") or not listing.get("is_visible", True):
            continue
        matched: set[tuple[str, str]] = set()
        for location in listing.get("locations") or []:
            match = LOCATION_PATTERN.match(str(location))
            if not match:
                continue
            key = (normalize_city_name(match.group("city")), match.group("state"))
            if key in city_lookup:
                matched.add(key)
        for key in matched:
            counts[key] += 1
            source_updated[key] = max(source_updated[key], int(listing.get("date_updated") or 0))
            city = city_lookup[key]
            detail_rows.append({
                "job_id": listing.get("id") or "",
                "city_slug": build_city_slug(str(city.city), str(city.state_id)),
                "county_fips": str(city.county_fips).zfill(5),
                "company_name": listing.get("company_name") or "",
                "title": listing.get("title") or "",
                "category": listing.get("category") or "",
                "location": next(
                    (str(value) for value in listing.get("locations") or []
                     if LOCATION_PATTERN.match(str(value)) and
                     (normalize_city_name(LOCATION_PATTERN.match(str(value)).group("city")),
                      LOCATION_PATTERN.match(str(value)).group("state")) == key),
                    "",
                ),
                "job_url": listing.get("url") or "",
                "date_posted": datetime.fromtimestamp(int(listing.get("date_posted") or 0), tz=timezone.utc).date().isoformat() if listing.get("date_posted") else "",
                "date_updated": datetime.fromtimestamp(int(listing.get("date_updated") or 0), tz=timezone.utc).date().isoformat() if listing.get("date_updated") else "",
                "sponsorship": listing.get("sponsorship") or "",
                "source": listing.get("source") or "",
                "source_repository": repository,
            })

    fetched_date = datetime.now(timezone.utc).date().isoformat()
    rows = []
    for key, row in city_lookup.items():
        updated = source_updated[key]
        source_date = (
            datetime.fromtimestamp(updated, tz=timezone.utc).date().isoformat()
            if updated else fetched_date
        )
        rows.append({
            "city_slug": build_city_slug(str(row.city), str(row.state_id)),
            "county_fips": str(row.county_fips).zfill(5),
            "newgrad_job_post_count": counts[key],
            "newgrad_job_board_count": 1,
            "newgrad_job_city_page_url": f"https://github.com/{repository}",
            "newgrad_jobs_source": "github_simplify_new_grad_positions",
            "newgrad_jobs_source_date": source_date,
            "newgrad_jobs_confidence": "source_backed",
            "newgrad_jobs_is_imputed": False,
            "has_newgrad_jobs_context": counts[key] > 0,
        })
    details = pd.DataFrame(detail_rows).drop_duplicates(subset=["job_id", "city_slug"])
    return pd.DataFrame(rows), details


def fetch_github_jobs(
    cities_path: Path,
    repository: str,
    listings_path: str,
    token: str = "",
    timeout: float = 20,
) -> pd.DataFrame:
    summary, _ = fetch_github_jobs_data(cities_path, repository, listings_path, token, timeout)
    return summary
