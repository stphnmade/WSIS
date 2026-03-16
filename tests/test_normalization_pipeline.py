from pathlib import Path

from wsis.data.pipeline.normalize import build_normalized_city_dataset


def test_normalized_dataset_builds_with_expected_join_keys(tmp_path: Path) -> None:
    output_path = tmp_path / "city_dataset.csv"

    records = build_normalized_city_dataset(output_path=output_path)

    assert output_path.exists()
    assert len(records) == 10
    assert len({record.city_slug for record in records}) == len(records)
    assert all(len(record.county_fips) == 5 for record in records)
    assert all(record.cost_source_name for record in records)
    assert all(record.jobs_source_name for record in records)


def test_normalized_dataset_preserves_city_anchor_county_mapping(tmp_path: Path) -> None:
    records = build_normalized_city_dataset(output_path=tmp_path / "city_dataset.csv")
    by_slug = {record.city_slug: record for record in records}

    assert by_slug["austin-tx"].county_fips == "48453"
    assert by_slug["chicago-il"].county_fips == "17031"

