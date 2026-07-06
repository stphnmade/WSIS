from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import pandas as pd
from pydantic import BaseModel, Field

from wsis.core.config import get_settings
from wsis.data.ingestion.common import normalize_city_name


PLACE_SUFFIX = re.compile(
    r"\s+(city|town|village|borough|municipality|cdp|urbana|comunidad|zona urbana)$",
    re.IGNORECASE,
)


class ExploreCity(BaseModel):
    place_geoid: str = Field(pattern=r"^\d{7}$")
    slug: str
    name: str
    state_code: str
    latitude: float
    longitude: float
    active_listing_count: int = Field(ge=0)
    latest_listing_date: str
    coverage_status: str = "job_feed_covered"


class PublicJobListing(BaseModel):
    job_id: str
    place_geoid: str
    place_name: str
    state_code: str
    company_name: str
    title: str
    category: str
    locations: str
    job_url: str
    date_posted: str
    date_updated: str
    sponsorship: str
    source: str


def _slug(name: str, state_code: str) -> str:
    return f"{normalize_city_name(name).replace(' ', '-')}-{state_code.lower()}"


class ExploreService:
    def __init__(self, processed_root: Path | None = None) -> None:
        settings = get_settings()
        root = processed_root or Path(settings.processed_city_profiles_path).parent
        self._coverage_path = root / "national_job_city_coverage.csv"
        self._jobs_path = root / "national_job_listings.csv"

    @lru_cache(maxsize=1)
    def _coverage(self) -> pd.DataFrame:
        if not self._coverage_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self._coverage_path, dtype={"place_geoid": str})

    @lru_cache(maxsize=1)
    def _jobs(self) -> pd.DataFrame:
        if not self._jobs_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self._jobs_path, dtype={"place_geoid": str}).fillna("")

    def list_places(
        self,
        limit: int = 100,
        query: str | None = None,
        state_code: str | None = None,
        role: str | None = None,
    ) -> list[ExploreCity]:
        frame = self._coverage().copy()
        if frame.empty:
            return []
        if role:
            jobs = self._jobs().copy()
            tokens = [token for token in normalize_city_name(role).split() if len(token) >= 3]
            if tokens and not jobs.empty:
                haystack = (jobs["title"] + " " + jobs["category"]).str.lower()
                matched = jobs[haystack.map(lambda value: any(token in value for token in tokens))]
                counts = matched.groupby("place_geoid").agg(
                    active_listing_count=("job_id", "nunique"),
                    latest_listing_date=("date_updated", "max"),
                ).reset_index()
                frame = frame.drop(columns=["active_listing_count", "latest_listing_date"]).merge(
                    counts, on="place_geoid", how="inner"
                )
            else:
                frame = frame.iloc[0:0]
        if state_code:
            frame = frame[frame["state_code"].str.upper() == state_code.upper()]
        if query:
            needle = normalize_city_name(query)
            frame = frame[
                frame["place_name"].map(normalize_city_name).str.contains(needle, regex=False)
                | frame["state_code"].str.lower().eq(query.lower())
            ]
        frame = frame.sort_values("active_listing_count", ascending=False).head(limit)
        rows = []
        for item in frame.to_dict("records"):
            name = PLACE_SUFFIX.sub("", str(item["place_name"]))
            rows.append(
                ExploreCity(
                    place_geoid=str(item["place_geoid"]).zfill(7),
                    slug=_slug(name, str(item["state_code"])),
                    name=name,
                    state_code=str(item["state_code"]),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    active_listing_count=int(item["active_listing_count"]),
                    latest_listing_date=str(item["latest_listing_date"]),
                )
            )
        return rows

    def list_jobs(self, place_geoid: str, limit: int = 50) -> list[PublicJobListing]:
        frame = self._jobs()
        if frame.empty:
            return []
        matched = frame[frame["place_geoid"] == place_geoid].head(limit)
        return [PublicJobListing.model_validate(item) for item in matched.to_dict("records")]


@lru_cache(maxsize=1)
def get_explore_service() -> ExploreService:
    return ExploreService()
