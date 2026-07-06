from io import BytesIO
from zipfile import ZipFile

from wsis.data.ingestion.census_places import fetch_census_places


class _Response:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        return None


def test_fetch_census_places_normalizes_geoids(monkeypatch) -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "places.txt",
            "USPS|GEOID|GEOIDFQ|ANSICODE|NAME|LSAD|FUNCSTAT|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG\n"
            "TX|4805000|1600000US4805000|123|Austin city|25|A|1|2|0|0|30.1|-97.1\n",
        )
    monkeypatch.setattr(
        "wsis.data.ingestion.census_places.requests.get",
        lambda *args, **kwargs: _Response(buffer.getvalue()),
    )

    result = fetch_census_places(2025)

    assert result.loc[0, "place_geoid"] == "4805000"
    assert result.loc[0, "place_name"] == "Austin city"
    assert result.loc[0, "state_code"] == "TX"
    assert result.loc[0, "source_vintage"] == 2025
