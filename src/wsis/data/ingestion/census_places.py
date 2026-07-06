from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import requests


GAZETTEER_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "{year}_Gazetteer/{year}_Gaz_place_national.zip"
)


def fetch_census_places(year: int = 2025, timeout: float = 30) -> pd.DataFrame:
    """Fetch the official national Census place gazetteer."""
    response = requests.get(GAZETTEER_URL.format(year=year), timeout=timeout)
    response.raise_for_status()
    with ZipFile(BytesIO(response.content)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(names) != 1:
            raise ValueError("Census place archive must contain exactly one text file")
        with archive.open(names[0]) as source:
            frame = pd.read_csv(
                source,
                sep="|",
                dtype={"GEOID": str, "USPS": str, "ANSICODE": str},
            )
    frame = frame.rename(
        columns={
            "USPS": "state_code",
            "GEOID": "place_geoid",
            "NAME": "place_name",
            "LSAD": "lsad_code",
            "FUNCSTAT": "functional_status",
            "ALAND": "land_area_sqm",
            "AWATER": "water_area_sqm",
            "INTPTLAT": "latitude",
            "INTPTLONG": "longitude",
        }
    )
    columns = [
        "place_geoid", "place_name", "state_code", "lsad_code",
        "functional_status", "land_area_sqm", "water_area_sqm",
        "latitude", "longitude",
    ]
    result = frame[columns].copy()
    result["place_geoid"] = result["place_geoid"].str.zfill(7)
    result["source_vintage"] = year
    result["source_url"] = GAZETTEER_URL.format(year=year)
    return result
