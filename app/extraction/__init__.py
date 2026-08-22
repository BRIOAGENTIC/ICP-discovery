from .extractor import (
    compute_relevance,
    detect_platform,
    extract_name,
    extract_role_company,
)
from .dedup import dedup

__all__ = [
    "compute_relevance",
    "detect_platform",
    "extract_name",
    "extract_role_company",
    "dedup",
]