#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

import pandas as pd
import requests

from wsis.data.ingestion.census_places import fetch_census_places
from wsis.data.ingestion.common import STATE_TO_REGION, normalize_city_name
from wsis.data.ingestion.github_jobs import GITHUB_API_URL, _headers


PLACE_SUFFIX = re.compile(
    r"\s+(city|town|village|borough|municipality|cdp|urbana|comunidad|zona urbana)$",
    re.IGNORECASE,
)
LOCATION_PATTERN = re.compile(r"^\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s*$")
CITY_ALIASES = {
    ("sf", "CA"): ("san francisco", "CA"),
    ("nyc", "NY"): ("new york", "NY"),
    ("dc", "DC"): ("washington", "DC"),
    ("boise", "ID"): ("boise city", "ID"),
    ("nashville", "TN"): ("nashville davidson metropolitan government balance", "TN"),
    ("indianapolis", "IN"): ("indianapolis city balance", "IN"),
}
US_STATE_CODES = set(STATE_TO_REGION) | {"DC"}


def _place_key(name: str, state_code: str, strip_suffix: bool = False) -> tuple[str, str]:
    clean_name = PLACE_SUFFIX.sub("", name.strip()) if strip_suffix else name.strip()
    key = (normalize_city_name(clean_name), state_code.upper())
    return CITY_ALIASES.get(key, key)


def _github_payload(repository: str, path: str, token: str, timeout: float) -> list[dict]:
    metadata = requests.get(
        GITHUB_API_URL.format(repository=repository, path=path),
        headers=_headers(token), timeout=timeout,
    )
    metadata.raise_for_status()
    download_url = metadata.json().get("download_url")
    if not download_url:
        raise ValueError("GitHub contents response did not include download_url")
    response = requests.get(download_url, headers=_headers(token), timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_coverage_artifacts(
    places: pd.DataFrame,
    listings: list[dict],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    keyed_places: dict[tuple[str, str], list[dict]] = {}
    places_by_geoid: dict[str, dict] = {}
    for row in places.to_dict("records"):
        keyed_places.setdefault(_place_key(row["place_name"], row["state_code"], True), []).append(row)
        places_by_geoid[str(row["place_geoid"])] = row

    counts: dict[str, int] = {}
    latest: dict[str, int] = {}
    unmatched: dict[str, int] = {}
    detail_rows: list[dict] = []
    active_count = 0
    location_count = 0
    for listing in listings:
        if not listing.get("active") or not listing.get("is_visible", True):
            continue
        active_count += 1
        matched_geoids: set[str] = set()
        for raw_location in listing.get("locations") or []:
            match = LOCATION_PATTERN.match(str(raw_location))
            if not match:
                continue
            if match.group("state") not in US_STATE_CODES:
                continue
            location_count += 1
            key = _place_key(match.group("city"), match.group("state"))
            candidates = keyed_places.get(key, [])
            active_incorporated = [
                candidate for candidate in candidates
                if candidate.get("functional_status") == "A" and candidate.get("lsad_code") != "57"
            ]
            if len(active_incorporated) == 1:
                candidates = active_incorporated
            if len(candidates) != 1:
                unmatched[str(raw_location)] = unmatched.get(str(raw_location), 0) + 1
                continue
            geoid = str(candidates[0]["place_geoid"])
            matched_geoids.add(geoid)
        for geoid in matched_geoids:
            counts[geoid] = counts.get(geoid, 0) + 1
            latest[geoid] = max(latest.get(geoid, 0), int(listing.get("date_updated") or 0))
            place = places_by_geoid[geoid]
            detail_rows.append(
                {
                    "job_id": listing.get("id") or "",
                    "place_geoid": geoid,
                    "place_name": PLACE_SUFFIX.sub("", str(place["place_name"])),
                    "state_code": place["state_code"],
                    "company_name": listing.get("company_name") or "",
                    "title": listing.get("title") or "",
                    "category": listing.get("category") or "",
                    "locations": " | ".join(str(item) for item in listing.get("locations") or []),
                    "job_url": listing.get("url") or "",
                    "date_posted": datetime.fromtimestamp(
                        int(listing.get("date_posted") or 0), tz=timezone.utc
                    ).date().isoformat() if listing.get("date_posted") else "",
                    "date_updated": datetime.fromtimestamp(
                        int(listing.get("date_updated") or 0), tz=timezone.utc
                    ).date().isoformat() if listing.get("date_updated") else "",
                    "sponsorship": listing.get("sponsorship") or "",
                    "source": listing.get("source") or "Simplify",
                }
            )

    coverage = places[places["place_geoid"].isin(counts)].copy()
    coverage["active_listing_count"] = coverage["place_geoid"].map(counts).astype(int)
    coverage["latest_listing_date"] = coverage["place_geoid"].map(
        lambda geoid: datetime.fromtimestamp(latest[geoid], tz=timezone.utc).date().isoformat()
        if latest.get(geoid) else ""
    )
    coverage = coverage.sort_values(
        ["active_listing_count", "state_code", "place_name"],
        ascending=[False, True, True],
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "census_place_count": int(len(places)),
        "active_source_listing_count": active_count,
        "parseable_us_location_count": location_count,
        "matched_place_count": int(len(coverage)),
        "matched_listing_assignments": int(coverage["active_listing_count"].sum()),
        "unmatched_location_count": int(sum(unmatched.values())),
        "top_unmatched_locations": [
            {"location": location, "count": count}
            for location, count in sorted(unmatched.items(), key=lambda item: item[1], reverse=True)[:50]
        ],
        "caveat": (
            "Listings are a partial early-career technology feed. Counts show source coverage, "
            "not total labor demand; government labor statistics remain authoritative."
        ),
    }
    details = pd.DataFrame(detail_rows).drop_duplicates(subset=["job_id", "place_geoid"])
    return coverage, details, report


def build_coverage(places: pd.DataFrame, listings: list[dict]) -> tuple[pd.DataFrame, dict]:
    coverage, _, report = build_coverage_artifacts(places, listings)
    return coverage, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit nationwide Census place coverage in the GitHub job feed")
    parser.add_argument("--year", type=int, default=int(os.getenv("WSIS_CENSUS_PLACES_YEAR", "2025")))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    timeout = float(os.getenv("WSIS_INGEST_TIMEOUT_SECONDS", "30"))
    repository = os.getenv("WSIS_GITHUB_JOBS_REPOSITORY", "SimplifyJobs/New-Grad-Positions")
    path = os.getenv("WSIS_GITHUB_JOBS_PATH", ".github/scripts/listings.json")

    places = fetch_census_places(args.year, timeout)
    listings = _github_payload(repository, path, os.getenv("GITHUB_TOKEN", ""), timeout)
    coverage, details, report = build_coverage_artifacts(places, listings)

    raw_path = root / "data" / "raw" / "census" / f"places_{args.year}.csv"
    coverage_path = root / "data" / "processed" / "national_job_city_coverage.csv"
    details_path = root / "data" / "processed" / "national_job_listings.csv"
    report_path = root / "data" / "processed" / "national_job_coverage_report.json"
    places.to_csv(raw_path, index=False)
    coverage.to_csv(coverage_path, index=False)
    details.to_csv(details_path, index=False)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
