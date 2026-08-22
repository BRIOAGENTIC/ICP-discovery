"""Deduplicate results by URL and by name."""
from typing import Dict, List

from app.models import ProfileResult


def dedup(items: List[ProfileResult]) -> List[ProfileResult]:
    seen_urls = set()
    seen_names = set()
    out: List[ProfileResult] = []
    for it in items:
        key_url = it.profile_url.rstrip("/").lower()
        if key_url in seen_urls:
            continue
        key_name = (it.name or "").strip().lower()
        if key_name and key_name in seen_names:
            continue
        seen_urls.add(key_url)
        if key_name:
            seen_names.add(key_name)
        out.append(it)
    return out