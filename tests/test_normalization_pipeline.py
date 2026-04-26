from pathlib import Path
import shutil

from wsis.data.pipeline.city_profiles import build_city_profiles_dataset
from wsis.core.config import get_settings


def test_city_profiles_dataset_builds_with_expected_join_keys(tmp_path: Path) -> None:
    output_path = tmp_path / "city_profiles.parquet"
    report_path = tmp_path / "city_profiles_validation_report.json"

    records = build_city_profiles_dataset(output_path=output_path, report_path=report_path)

    assert output_path.exists()
    assert report_path.exists()
    assert len(records) == 10
    assert len({record.city_slug for record in records}) == len(records)
    assert all(len(record.county_fips) == 5 for record in records)
    assert all(0 <= record.affordability_norm <= 1 for record in records)
    assert all(record.is_mvp_eligible for record in records)
    assert all(isinstance(record.is_warm, bool) for record in records)
    assert all(record.has_hud_fmr_data for record in records)
    assert all(record.fair_market_rent > 0 for record in records)
    assert any(record.education_bachelors_pct > 0 for record in records)
    assert all(record.has_newgrad_jobs_context for record in records)
    assert any(record.newgrad_job_board_count > 0 for record in records)


def test_city_profiles_dataset_handles_missing_optional_source(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(Path("data/raw"), raw_root)
    (raw_root / "noaa" / "county_climate.csv").unlink()

    records = build_city_profiles_dataset(
        raw_root=raw_root,
        output_path=tmp_path / "city_profiles.parquet",
        report_path=tmp_path / "city_profiles_validation_report.json",
    )
    by_slug = {record.city_slug: record for record in records}

    assert by_slug["austin-tx"].has_noaa_data is False
    assert by_slug["austin-tx"].climate_confidence == "estimated"
    assert by_slug["austin-tx"].is_mvp_eligible is False
    assert by_slug["austin-tx"].climate_score_raw >= 0


def test_city_profiles_dataset_handles_missing_hud_source(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(Path("data/raw"), raw_root)
    (raw_root / "hud" / "fair_market_rents.csv").unlink()

    records = build_city_profiles_dataset(
        raw_root=raw_root,
        output_path=tmp_path / "city_profiles.parquet",
        report_path=tmp_path / "city_profiles_validation_report.json",
    )
    by_slug = {record.city_slug: record for record in records}

    assert by_slug["austin-tx"].has_hud_fmr_data is False
    assert by_slug["austin-tx"].fair_market_rent_is_imputed is True
    assert by_slug["austin-tx"].affordability_confidence == "estimated"
    assert by_slug["austin-tx"].is_mvp_eligible is False


def test_city_profiles_dataset_uses_newgrad_seed_when_scrape_fails(tmp_path: Path, monkeypatch) -> None:
    raw_root = tmp_path / "raw"
    source_root = tmp_path / "source_samples"
    shutil.copytree(Path("data/raw"), raw_root)
    shutil.copytree(Path("data/source_samples"), source_root)
    monkeypatch.setenv("WSIS_NEWGRAD_JOBS_BASE_URL", "https://127.0.0.1:1")
    monkeypatch.setenv("WSIS_NEWGRAD_JOBS_TIMEOUT_SECONDS", "0.1")
    get_settings.cache_clear()

    records = build_city_profiles_dataset(
        raw_root=raw_root,
        source_samples_root=source_root,
        output_path=tmp_path / "city_profiles.parquet",
        report_path=tmp_path / "city_profiles_validation_report.json",
    )
    by_slug = {record.city_slug: record for record in records}

    assert by_slug["austin-tx"].has_newgrad_jobs_context is True
    assert by_slug["austin-tx"].newgrad_jobs_source == "newgrad_jobs_local_seed"
    assert by_slug["austin-tx"].newgrad_jobs_is_imputed is True
    get_settings.cache_clear()
