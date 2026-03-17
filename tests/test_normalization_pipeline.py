from pathlib import Path
import shutil

from wsis.data.pipeline.city_profiles import build_city_profiles_dataset


def test_city_profiles_dataset_builds_with_expected_join_keys(tmp_path: Path) -> None:
    output_path = tmp_path / "city_profiles.parquet"

    records = build_city_profiles_dataset(output_path=output_path)

    assert output_path.exists()
    assert len(records) == 10
    assert len({record.city_slug for record in records}) == len(records)
    assert all(len(record.county_fips) == 5 for record in records)
    assert all(0 <= record.affordability_norm <= 1 for record in records)


def test_city_profiles_dataset_handles_missing_optional_source(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(Path("data/raw"), raw_root)
    (raw_root / "noaa" / "county_climate.csv").unlink()

    records = build_city_profiles_dataset(
        raw_root=raw_root,
        output_path=tmp_path / "city_profiles.parquet",
    )
    by_slug = {record.city_slug: record for record in records}

    assert by_slug["austin-tx"].has_noaa_data is False
    assert by_slug["austin-tx"].climate_score_raw >= 0
