from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class OccupationFamily(str, Enum):
    TECH = "tech"
    DATA = "data"
    PRODUCT = "product"
    DESIGN = "design"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    FEDERAL = "federal"
    OTHER = "other"


@dataclass(frozen=True)
class OccupationMapping:
    family: OccupationFamily
    soc_family_codes: tuple[str, ...]
    matched_keyword: str | None
    confidence: str


# Broad SOC groups are scaffolding, not a claim that every title maps to every
# code listed. A later O*NET crosswalk can replace these deterministic rules.
_FAMILY_RULES: tuple[tuple[OccupationFamily, tuple[str, ...], tuple[str, ...]], ...] = (
    # Federal is an employer sector, not an SOC occupation; keep codes empty
    # until the title itself can be mapped to an occupation.
    (OccupationFamily.FEDERAL, (), ("federal", "government affairs", "public sector", "civil service")),
    (OccupationFamily.DATA, ("15", "17-2112"), ("data", "analytics", "machine learning", "business intelligence", "bi analyst")),
    (OccupationFamily.PRODUCT, ("11-2021", "13-1082"), ("product manager", "product owner", "product management", "program manager")),
    (OccupationFamily.DESIGN, ("15-1255", "27-1024"), ("designer", "user experience", "ux", "ui", "design researcher")),
    (OccupationFamily.MARKETING, ("11-2021", "13-1161"), ("marketing", "growth", "seo", "communications", "brand")),
    (OccupationFamily.OPERATIONS, ("11-1021", "13-1082"), ("operations", "supply chain", "logistics", "business operations", "project manager")),
    (OccupationFamily.TECH, ("15",), ("software", "developer", "engineer", "cyber", "security", "devops", "cloud", "systems administrator", "it support")),
)


def map_occupation_family(title: str, description: str = "") -> OccupationMapping:
    text = re.sub(r"\s+", " ", f"{title} {description}".lower())
    for family, soc_codes, keywords in _FAMILY_RULES:
        for keyword in keywords:
            if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text):
                confidence = "sector_keyword" if family is OccupationFamily.FEDERAL else "keyword_rule"
                return OccupationMapping(family, soc_codes, keyword, confidence)
    return OccupationMapping(OccupationFamily.OTHER, (), None, "unmapped")
