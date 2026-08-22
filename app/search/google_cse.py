"""Google Custom Search JSON API client with retry + pagination."""
import logging
from typing import Any, Dict, List

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleCSEError(Exception):
    pass


class GoogleCSEClient:
    def __init__(self) -> None:
        if not settings.google_api_key or not settings.google_cse_id:
            raise GoogleCSEError(
                "GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in .env"
            )
        self._client = httpx.AsyncClient(
            timeout=settings.google_cse_timeout_seconds
        )

    @retry(
        retry=retry_if_exception_type(
            (httpx.TransportError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _raw_search(
        self, query: str, start: int
    ) -> Dict[str, Any]:
        params = {
            "key": settings.google_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "start": start,
            "num": 10,
        }
        logger.info("Google CSE query start=%s q=%s", start, query)
        resp = await self._client.get(GOOGLE_CSE_URL, params=params)
        if resp.status_code == 429:
            logger.error("Google CSE quota exceeded (429).")
            raise GoogleCSEError("Google CSE quota exceeded (429).")
        resp.raise_for_status()
        return resp.json()

    async def search(
        self, query: str, max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """Paginate Google CSE up to max_pages (10 results per page)."""
        all_items: List[Dict[str, Any]] = []
        for page_idx in range(max_pages):
            start = page_idx * 10 + 1
            try:
                data = await self._raw_search(query, start=start)
            except Exception as e:
                logger.error(
                    "Search failed for query=%r start=%s: %s",
                    query, start, e
                )
                break
            items = data.get("items", [])
            if not items:
                break
            all_items.extend(items)
        return all_items

    async def aclose(self) -> None:
        await self._client.aclose()


# Singleton
cse_client = GoogleCSEClient()