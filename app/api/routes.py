"""API routes."""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.cache import cache
from app.config import settings
from app.extraction import (
    compute_relevance,
    dedup,
    detect_platform,
    extract_name,
)
from app.models import (
    ICPSearchRequest,
    ICPSearchResponse,
    ProfileResult,
)
from app.search import build_queries, tavily_client

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_profile(raw_item: dict, req: ICPSearchRequest) -> ProfileResult:
    title = raw_item.get("title", "")
    snippet = raw_item.get("content", "")
    url = raw_item.get("url", "")
    platform = detect_platform(url)
    name = extract_name(title, snippet, platform)
    score = compute_relevance(title, snippet, req)
    # Combined snippet includes title for richer context
    combined = f"{title} — {snippet}".strip(" —")
    return ProfileResult(
        name=name,
        source_platform=platform,
        profile_url=url,
        matched_snippet=combined[:500],
        relevance_score=score,
    )


@router.post("/profiles/search", response_model=ICPSearchResponse)
async def search_profiles(req: ICPSearchRequest, request: Request) -> ICPSearchResponse:
    """Discover people matching an Ideal Customer Profile across the open web."""
    cache_key = {
        "industry": req.industry,
        "job_title": req.job_title,
        "company_size": req.company_size,
        "location": req.location,
        "keywords": req.keywords,
    }

    cached = cache.get(cache_key)
    if cached is None:
        logger.info("Cache miss; running search for %s", cache_key)
        queries = build_queries(req)
        all_items: List[dict] = []
        for q in queries:
            try:
                items = await tavily_client.search(q, max_results=20)
                all_items.extend(items)
            except Exception as e:
                logger.error("Query %r failed: %s", q, e)
                # Continue with other queries rather than failing hard

        profiles = [_to_profile(it, req) for it in all_items]
        profiles = dedup(profiles)
        # Sort by score desc for stable pagination
        profiles.sort(key=lambda p: p.relevance_score, reverse=True)
        cache.set(cache_key, [p.model_dump() for p in profiles])
        cached = [p.model_dump() for p in profiles]
    else:
        logger.info("Cache hit for %s", cache_key)

    total = len(cached)
    start = (req.page - 1) * req.limit
    end = start + req.limit
    page_items = cached[start:end]

    return ICPSearchResponse(
        page=req.page,
        limit=req.limit,
        total_found=total,
        results=[ProfileResult(**p) for p in page_items],
    )


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
