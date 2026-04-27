#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from wsis.core.config import get_settings
from wsis.data.pipeline.city_profiles import build_city_profiles_dataset
from wsis.data.validation import validate_city_profiles_file


def main() -> int:
    settings = get_settings()
    output_path = Path(settings.processed_city_profiles_path)
    report_path = Path(settings.city_profiles_validation_report_path)

    records = build_city_profiles_dataset(output_path=output_path, report_path=report_path)
    validate_city_profiles_file(output_path)

    print(f"Built and validated {len(records)} city profiles.")
    print(f"Dataset: {output_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
