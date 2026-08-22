"""Tavily Search API client with retry and lazy singleton."""
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

TAVILY_URL = "https://api.tavily.com/search"


class TavilyError(Exception):
    pass


class TavilyClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=settings.tavily_timeout_seconds)
        return self._client

    @retry(
        retry=retry_if_exception_type(
            (httpx.TransportError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _raw_search(
        self, query: str, max_results: int
    ) -> Dict[str, Any]:
        if not settings.tavily_api_key:
            raise TavilyError("TAVILY_API_KEY must be set in .env")
        
        client = await self._get_client()
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }
        logger.info("Tavily query max_results=%s q=%s", max_results, query)
        resp = await client.post(TAVILY_URL, json=payload)
        
        if resp.status_code == 429:
            logger.error("Tavily quota exceeded (429).")
            # Raise HTTPStatusError so tenacity can catch and retry it
            resp.raise_for_status()
            
        resp.raise_for_status()
        return resp.json()

    async def search(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        try:
            data = await self._raw_search(query, max_results=max_results)
        except Exception as e:
            logger.error(
                "Search failed for query=%r: %s",
                query, e
            )
            return []
        return data.get("results", [])

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


tavily_client = TavilyClient()
