from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import re


class SalaryPeriod(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SalaryBand(str, Enum):
    BELOW_40K = "below_40k"
    FROM_40K_TO_60K = "40k_60k"
    FROM_60K_TO_90K = "60k_90k"
    FROM_90K_TO_130K = "90k_130k"
    FROM_130K_TO_180K = "130k_180k"
    ABOVE_180K = "above_180k"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NormalizedSalary:
    annual_min: int | None
    annual_max: int | None
    currency: str
    source_period: SalaryPeriod
    band: SalaryBand
    confidence: str


_MULTIPLIER = {
    SalaryPeriod.HOUR: Decimal("2080"),
    SalaryPeriod.DAY: Decimal("260"),
    SalaryPeriod.WEEK: Decimal("52"),
    SalaryPeriod.MONTH: Decimal("12"),
    SalaryPeriod.YEAR: Decimal("1"),
}


def salary_band(annual_midpoint: int | None) -> SalaryBand:
    if annual_midpoint is None:
        return SalaryBand.UNKNOWN
    if annual_midpoint < 40_000:
        return SalaryBand.BELOW_40K
    if annual_midpoint < 60_000:
        return SalaryBand.FROM_40K_TO_60K
    if annual_midpoint < 90_000:
        return SalaryBand.FROM_60K_TO_90K
    if annual_midpoint < 130_000:
        return SalaryBand.FROM_90K_TO_130K
    if annual_midpoint < 180_000:
        return SalaryBand.FROM_130K_TO_180K
    return SalaryBand.ABOVE_180K


def _annualize(value: int | float | Decimal, period: SalaryPeriod) -> int:
    amount = Decimal(str(value)) * _MULTIPLIER[period]
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def normalize_salary(
    minimum: int | float | Decimal | None,
    maximum: int | float | Decimal | None,
    period: SalaryPeriod | str = SalaryPeriod.YEAR,
    currency: str = "USD",
) -> NormalizedSalary:
    source_period = SalaryPeriod(period)
    if minimum is None and maximum is None:
        return NormalizedSalary(None, None, currency.upper(), source_period, SalaryBand.UNKNOWN, "missing")
    annual_min = _annualize(minimum, source_period) if minimum is not None else None
    annual_max = _annualize(maximum, source_period) if maximum is not None else None
    if annual_min is None:
        annual_min = annual_max
    if annual_max is None:
        annual_max = annual_min
    if annual_min is not None and annual_max is not None and annual_min > annual_max:
        annual_min, annual_max = annual_max, annual_min
    midpoint = (annual_min + annual_max) // 2 if annual_min is not None and annual_max is not None else None
    confidence = "source_backed" if currency.upper() == "USD" else "unconverted_currency"
    return NormalizedSalary(annual_min, annual_max, currency.upper(), source_period, salary_band(midpoint), confidence)


_SALARY_VALUE = r"\$?\s*(\d+(?:\.\d+)?)\s*([kK]?)"
_PERIOD_ALIASES = {
    "hour": SalaryPeriod.HOUR, "hr": SalaryPeriod.HOUR,
    "day": SalaryPeriod.DAY, "week": SalaryPeriod.WEEK,
    "month": SalaryPeriod.MONTH, "mo": SalaryPeriod.MONTH,
    "year": SalaryPeriod.YEAR, "yr": SalaryPeriod.YEAR, "annual": SalaryPeriod.YEAR,
}


def parse_salary_text(value: str, currency: str = "USD") -> NormalizedSalary:
    """Parse common source ranges such as ``$80k-$100k/year``."""
    values = re.findall(_SALARY_VALUE, value)
    if not values:
        return normalize_salary(None, None, currency=currency)
    amounts = [Decimal(number) * (1000 if suffix else 1) for number, suffix in values[:2]]
    period_match = re.search(r"(?:per|/|a\s+)?\s*(hour|hr|day|week|month|mo|year|yr|annual)(?:ly)?\b", value, re.IGNORECASE)
    period = _PERIOD_ALIASES[period_match.group(1).lower()] if period_match else SalaryPeriod.YEAR
    return normalize_salary(amounts[0], amounts[-1], period, currency)
