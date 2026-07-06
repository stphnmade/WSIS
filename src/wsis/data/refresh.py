from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path

import pandas as pd
import requests

from wsis.core.config import get_settings
from wsis.data.ingestion.common import load_raw_csv, normalize_city_name
from wsis.data.ingestion.github_jobs import fetch_github_jobs_data
from wsis.data.ingestion.github_geography import fetch_github_geography


STATE_FIPS = {
    "AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09","DE":"10","DC":"11",
    "FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18","IA":"19","KS":"20","KY":"21",
    "LA":"22","ME":"23","MD":"24","MA":"25","MI":"26","MN":"27","MS":"28","MO":"29","MT":"30",
    "NE":"31","NV":"32","NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39",
    "OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47","TX":"48","UT":"49",
    "VT":"50","VA":"51","WA":"53","WV":"54","WI":"55","WY":"56",
}
ACS_VARIABLES = "NAME,DP05_0001E,DP03_0062E,DP04_0134E,DP02_0068PE,DP03_0025E"


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def refresh_census(cities: pd.DataFrame, year: int, api_key: str, timeout: float) -> pd.DataFrame:
    if not api_key:
        raise RuntimeError("CENSUS_API_KEY is required by the Census API")
    records: dict[tuple[str, str], list[str]] = {}
    for state_code in sorted(set(cities["state_id"])):
        params = {"get": ACS_VARIABLES, "for": "place:*", "in": f"state:{STATE_FIPS[state_code]}"}
        if api_key:
            params["key"] = api_key
        response = requests.get(f"https://api.census.gov/data/{year}/acs/acs5/profile", params=params, timeout=timeout)
        response.raise_for_status()
        if "json" not in response.headers.get("content-type", "").lower():
            raise RuntimeError(f"Census API returned {response.headers.get('content-type', 'unknown content')}")
        values = response.json()
        for row in values[1:]:
            city = row[0].split(" city,")[0].split(" town,")[0].split(" village,")[0]
            records[(normalize_city_name(city), state_code)] = row
    rows = []
    for city in cities.itertuples(index=False):
        values = records.get((normalize_city_name(str(city.city)), str(city.state_id)))
        if not values:
            continue
        rows.append({"city":city.city,"state_id":city.state_id,"county_fips":str(city.county_fips).zfill(5),
                     "population":values[1],"median_income":values[2],"median_rent":values[3],
                     "education_bachelors_pct":values[4],"mean_commute_minutes":values[5]})
    return pd.DataFrame(rows)


def refresh_bls(cities: pd.DataFrame, api_key: str, timeout: float) -> pd.DataFrame:
    series_to_county = {f"LAUCN{str(fips).zfill(5)}0000000003": str(fips).zfill(5) for fips in cities["county_fips"]}
    payload = {"seriesid": list(series_to_county), "startyear": str(datetime.now().year - 1), "endyear": str(datetime.now().year)}
    if api_key:
        payload["registrationkey"] = api_key
    response = requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if body.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError("; ".join(body.get("message") or ["BLS request failed"]))
    rows = []
    for series in body["Results"]["series"]:
        monthly = [item for item in series.get("data", []) if item.get("period", "").startswith("M") and item.get("period") != "M13"]
        if monthly:
            latest = max(monthly, key=lambda item: (int(item["year"]), item["period"]))
            rows.append({"county_fips":series_to_county[series["seriesID"]], "unemployment_pct":latest["value"]})
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh WSIS geography, Census, BLS, and jobs inputs")
    parser.add_argument("--source", choices=["all", "github-geography", "census", "bls", "github-jobs"], default="all")
    args = parser.parse_args()
    settings = get_settings(); raw = Path(settings.raw_data_dir)
    cities = load_raw_csv(raw / "simplemaps" / "us_cities.csv", dtype={"county_fips": str})
    if cities.empty:
        raise RuntimeError("Canonical city file is empty")
    timeout = float(os.getenv("WSIS_INGEST_TIMEOUT_SECONDS", "30"))
    errors: list[str] = []
    if args.source in ("all", "github-geography"):
        try:
            frame = fetch_github_geography(
                raw / "simplemaps" / "us_cities.csv",
                os.getenv("WSIS_GITHUB_GEOGRAPHY_REPOSITORY", "dr5hn/countries-states-cities-database"),
                os.getenv("WSIS_GITHUB_GEOGRAPHY_PATH", "contributions/cities/US.json"),
                os.getenv("GITHUB_TOKEN", ""), timeout,
            )
            _write_csv(frame, raw / "github" / "us_cities.csv")
            cities = frame
            print(f"GitHub geography: {len(frame)} cities")
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            errors.append(f"GitHub geography: {exc}"); print(f"GitHub geography skipped: {exc}")
    if args.source in ("all", "census"):
        try:
            frame = refresh_census(cities, int(os.getenv("WSIS_CENSUS_ACS_YEAR", "2024")), os.getenv("CENSUS_API_KEY", ""), timeout)
            _write_csv(frame, raw / "census" / "acs_city_metrics.csv"); print(f"Census: {len(frame)} cities")
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            errors.append(f"Census: {exc}"); print(f"Census skipped: {exc}")
    if args.source in ("all", "bls"):
        try:
            frame = refresh_bls(cities, os.getenv("BLS_API_KEY", ""), timeout)
            _write_csv(frame, raw / "bls" / "county_unemployment.csv"); print(f"BLS: {len(frame)} counties")
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            errors.append(f"BLS: {exc}"); print(f"BLS skipped: {exc}")
    if args.source in ("all", "github-jobs"):
        try:
            frame, details = fetch_github_jobs_data(raw / "github" / "us_cities.csv" if (raw / "github" / "us_cities.csv").exists() else raw / "simplemaps" / "us_cities.csv", os.getenv("WSIS_GITHUB_JOBS_REPOSITORY", "SimplifyJobs/New-Grad-Positions"), os.getenv("WSIS_GITHUB_JOBS_PATH", ".github/scripts/listings.json"), os.getenv("GITHUB_TOKEN", ""), timeout)
            _write_csv(frame, raw / "github" / "newgrad_jobs.csv"); print(f"GitHub jobs: {len(frame)} cities, {int(frame.newgrad_job_post_count.sum())} listings")
            _write_csv(details, raw / "github" / "newgrad_job_listings.csv")
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            errors.append(f"GitHub jobs: {exc}"); print(f"GitHub jobs skipped: {exc}")
    if errors and args.source != "all":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
