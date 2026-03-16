from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


def load_csv_records(path: Path, model: type[ModelT]) -> tuple[ModelT, ...]:
    frame = pd.read_csv(path, dtype={"county_fips": str})
    return tuple(model.model_validate(record) for record in frame.to_dict("records"))

