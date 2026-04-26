from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import os
import re
from urllib.parse import urljoin

import pandas as pd
import requests

from wsis.core.config import get_settings
from wsis.data.ingestion.common import build_city_slug, load_raw_csv, normalize_city_name


DEFAULT_BASE_URL = "https://www.newgrad-jobs.com"
ENTRY_LEVEL_PATH = "/entry-level-jobs"
DEFAULT_TIMEOUT_SECONDS = 5.0
USER_AGENT = "WSISBot/0.1 (+local development)"


@dataclass(frozen=True)
class CanonicalCity:
    city_slug: str
    city_name: str
    state_code: str
    county_fips: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def _source_date_now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _configured_base_url() -> str:
    return get_settings().newgrad_jobs_base_url.rstrip("/") or DEFAULT_BASE_URL


def _configured_timeout() -> float:
    return get_settings().newgrad_jobs_timeout_seconds or DEFAULT_TIMEOUT_SECONDS


def _city_page_slug(city_name: str) -> str:
    normalized = normalize_city_name(city_name).replace(" ", "-")
    aliases = {
        "new-york": "nyc",
        "san-francisco": "san-rancisco",
        "washington": "washington-dc",
    }
    return aliases.get(normalized, normalized)


def _read_canonical_cities(raw_root: Path) -> tuple[CanonicalCity, ...]:
    frame = load_raw_csv(raw_root / "simplemaps" / "us_cities.csv", dtype={"county_fips": str})
    if frame.empty:
        return ()

    cities: list[CanonicalCity] = []
    for row in frame.to_dict("records"):
        city_name = str(row["city"])
        state_code = str(row["state_id"])
        cities.append(
            CanonicalCity(
                city_slug=build_city_slug(city_name, state_code),
                city_name=city_name,
                state_code=state_code,
                county_fips=str(row["county_fips"]).zfill(5),
            )
        )
    return tuple(cities)


def _fetch_text(url: str, timeout: float) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": os.getenv("WSIS_NEWGRAD_JOBS_USER_AGENT", USER_AGENT)},
    )
    response.raise_for_status()
    return response.text


def _extract_listing_urls(sitemap_text: str) -> tuple[str, ...]:
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap_text, flags=re.IGNORECASE)
    return tuple(url for url in urls if "/entry-level-jobs/" in url or "/list-" in url)


def _extract_entry_links(html_text: str, base_url: str) -> set[str]:
    parser = _LinkParser()
    parser.feed(html_text)
    return {
        urljoin(base_url, href)
        for href in parser.links
        if "/entry-level-jobs/" in href
    }


def _job_url_matches_city(url: str, city: CanonicalCity) -> bool:
    normalized_city = normalize_city_name(city.city_name).replace(" ", "_")
    state = city.state_code.lower()
    lower_url = url.lower()
    city_state_tokens = (
        f"{normalized_city}_{state}",
        f"{normalized_city}-{state}",
        f"{normalized_city}%2c_{state}",
    )
    if any(token in lower_url for token in city_state_tokens):
        return True
    if f"/entry-level-jobs/{_city_page_slug(city.city_name)}" in lower_url:
        return True
    return False


def _scrape_newgrad_rows(raw_root: Path, base_url: str, timeout: float) -> pd.DataFrame:
    cities = _read_canonical_cities(raw_root)
    if not cities:
        return pd.DataFrame()

    source_date = _source_date_now()
    entry_url = f"{base_url}{ENTRY_LEVEL_PATH}"
    sitemap_url = f"{base_url}/sitemap.xml"
    entry_links = _extract_entry_links(_fetch_text(entry_url, timeout), base_url)
    listing_urls = _extract_listing_urls(_fetch_text(sitemap_url, timeout))

    rows = []
    for city in cities:
        page_slug = _city_page_slug(city.city_name)
        city_page_url = f"{base_url}{ENTRY_LEVEL_PATH}/{page_slug}"
        has_city_page = city_page_url in entry_links or city_page_url in listing_urls
        matched_urls = [url for url in listing_urls if _job_url_matches_city(url, city)]
        rows.append(
            {
                "city_slug": city.city_slug,
                "county_fips": city.county_fips,
                "newgrad_job_post_count": len(matched_urls),
                "newgrad_job_board_count": 1 if has_city_page else 0,
                "newgrad_job_city_page_url": city_page_url if has_city_page else "",
                "newgrad_jobs_source": "newgrad_jobs_sitemap_scrape",
                "newgrad_jobs_source_date": source_date,
                "newgrad_jobs_confidence": "seeded",
                "newgrad_jobs_is_imputed": False,
                "has_newgrad_jobs_context": bool(has_city_page or matched_urls),
            }
        )
    return pd.DataFrame(rows)


def _seed_rows(source_root: Path) -> pd.DataFrame:
    frame = load_raw_csv(
        source_root / "newgrad_jobs.csv",
        dtype={"county_fips": str, "city_slug": str},
    )
    if frame.empty:
        return pd.DataFrame()

    seed = frame.copy()
    seed["county_fips"] = seed["county_fips"].astype("string").str.zfill(5)
    seed["newgrad_jobs_source"] = "newgrad_jobs_local_seed"
    seed["newgrad_jobs_source_date"] = (
        datetime.fromtimestamp((source_root / "newgrad_jobs.csv").stat().st_mtime, tz=timezone.utc)
        .date()
        .isoformat()
    )
    seed["newgrad_jobs_confidence"] = "seeded"
    seed["newgrad_jobs_is_imputed"] = True
    seed["has_newgrad_jobs_context"] = True
    return seed


def _fallback_or_fill(scraped: pd.DataFrame, seed: pd.DataFrame) -> pd.DataFrame:
    if scraped.empty:
        return seed
    if seed.empty:
        return scraped

    seed_by_slug = seed.set_index("city_slug")
    filled = scraped.copy()
    for index, row in filled.iterrows():
        if bool(row["has_newgrad_jobs_context"]):
            continue
        city_slug = str(row["city_slug"])
        if city_slug not in seed_by_slug.index:
            continue
        fallback = seed_by_slug.loc[city_slug]
        for column in [
            "newgrad_job_post_count",
            "newgrad_job_board_count",
            "newgrad_job_city_page_url",
            "newgrad_jobs_source",
            "newgrad_jobs_source_date",
            "newgrad_jobs_confidence",
            "newgrad_jobs_is_imputed",
            "has_newgrad_jobs_context",
        ]:
            filled.at[index, column] = fallback[column]
    return filled


def load_newgrad_jobs_context(raw_root: Path, source_root: Path) -> pd.DataFrame:
    seed = _seed_rows(source_root)
    try:
        scraped = _scrape_newgrad_rows(
            raw_root=raw_root,
            base_url=_configured_base_url(),
            timeout=_configured_timeout(),
        )
    except requests.RequestException:
        scraped = pd.DataFrame()

    frame = _fallback_or_fill(scraped, seed)
    expected_columns = [
        "city_slug",
        "county_fips",
        "newgrad_job_post_count",
        "newgrad_job_board_count",
        "newgrad_job_city_page_url",
        "newgrad_jobs_source",
        "newgrad_jobs_source_date",
        "newgrad_jobs_confidence",
        "newgrad_jobs_is_imputed",
        "has_newgrad_jobs_context",
    ]
    if frame.empty:
        return pd.DataFrame(columns=expected_columns)
    return frame[expected_columns]
