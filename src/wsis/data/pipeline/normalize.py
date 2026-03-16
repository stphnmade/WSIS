from __future__ import annotations

from pathlib import Path

import pandas as pd

from wsis.core.config import get_settings
from wsis.data.models import CanonicalCityRecord
from wsis.data.sources.city_index import load_city_index
from wsis.data.sources.climate import load_climate
from wsis.data.sources.cost_of_living import load_cost_of_living
from wsis.data.sources.jobs import load_jobs
from wsis.data.sources.safety import load_safety
from wsis.data.sources.social_sentiment import load_social_sentiment


def _frame_from_records(records: tuple[object, ...]) -> pd.DataFrame:
    return pd.DataFrame([record.model_dump() for record in records])


def build_normalized_city_dataset(
    source_dir: Path | None = None,
    output_path: Path | None = None,
) -> tuple[CanonicalCityRecord, ...]:
    settings = get_settings()
    base_source_dir = source_dir or Path(settings.source_data_dir)
    base_output_path = output_path or Path(settings.normalized_city_data_path)

    city_index = _frame_from_records(load_city_index(base_source_dir / "city_index.csv"))
    cost = _frame_from_records(load_cost_of_living(base_source_dir / "cost_of_living.csv"))
    jobs = _frame_from_records(load_jobs(base_source_dir / "jobs.csv"))
    safety = _frame_from_records(load_safety(base_source_dir / "safety.csv"))
    climate = _frame_from_records(load_climate(base_source_dir / "climate.csv"))
    social = _frame_from_records(load_social_sentiment(base_source_dir / "social_sentiment.csv"))

    normalized = (
        city_index.merge(cost, on="county_fips", how="left", validate="one_to_one")
        .merge(
            jobs.rename(
                columns={
                    "source_name": "jobs_source_name",
                    "source_vintage": "jobs_source_vintage",
                    "source_geography": "jobs_source_geography",
                }
            ),
            on="county_fips",
            how="left",
            validate="one_to_one",
        )
        .merge(
            safety.rename(
                columns={
                    "source_name": "safety_source_name",
                    "source_vintage": "safety_source_vintage",
                    "source_geography": "safety_source_geography",
                }
            ),
            on="county_fips",
            how="left",
            validate="one_to_one",
        )
        .merge(
            climate.rename(
                columns={
                    "source_name": "climate_source_name",
                    "source_vintage": "climate_source_vintage",
                    "source_geography": "climate_source_geography",
                }
            ),
            on="county_fips",
            how="left",
            validate="one_to_one",
        )
        .merge(
            social.rename(
                columns={
                    "source_name": "social_source_name",
                    "source_vintage": "social_source_vintage",
                    "source_geography": "social_source_geography",
                }
            ),
            on=["city_slug", "county_fips"],
            how="left",
            validate="one_to_one",
        )
    )

    normalized = normalized.rename(
        columns={
            "source_name": "cost_source_name",
            "source_vintage": "cost_source_vintage",
            "source_geography": "cost_source_geography",
        }
    )

    required_columns = [
        "city_slug",
        "county_fips",
        "county_name",
        "name",
        "state",
        "state_code",
        "region",
        "headline",
        "population",
        "latitude",
        "longitude",
        "known_for",
        "median_rent",
        "median_home_price",
        "median_income",
        "job_growth_pct",
        "unemployment_pct",
        "safety_score_raw",
        "climate_score_raw",
        "social_sentiment_raw",
        "cost_source_name",
        "jobs_source_name",
        "safety_source_name",
        "climate_source_name",
        "social_source_name",
    ]

    missing_columns = normalized[required_columns].isnull().any()
    if missing_columns.any():
        missing = ", ".join(column for column, is_missing in missing_columns.items() if is_missing)
        raise ValueError(f"Normalized dataset is missing required values for columns: {missing}")

    normalized = normalized.sort_values("city_slug").reset_index(drop=True)
    base_output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(base_output_path, index=False)

    return tuple(
        CanonicalCityRecord.model_validate(record)
        for record in normalized[required_columns].to_dict("records")
    )


def main() -> None:
    records = build_normalized_city_dataset()
    print(f"Built normalized city dataset with {len(records)} records.")


if __name__ == "__main__":
    main()

