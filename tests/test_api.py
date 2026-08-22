"""Smoke tests that don't hit Google CSE (FastAPI TestClient)."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_search_validation():
    with TestClient(app) as c:
        r = c.post("/profiles/search", json={"industry": "", "job_title": ""})
        assert r.status_code == 422


def test_search_with_mocked_cse():
    fake_items = [
        {
            "title": "Jane Doe - Senior PM at Acme | LinkedIn",
            "link": "https://www.linkedin.com/in/janedoe",
            "snippet": "Senior Product Manager at Acme (SaaS). Building AI tooling.",
        },
        {
            "title": "@janedoe (Jane Doe)",
            "link": "https://x.com/janedoe",
            "snippet": "PM at Acme. Talking about B2B SaaS.",
        },
    ]

    async def fake_search(self, query, max_pages=3):
        return list(fake_items)

    with patch("app.search.cse_client.search", new=AsyncMock(side_effect=fake_search)), \
         patch("app.api.routes.cache.get", return_value=None), \
         patch("app.api.routes.cache.set", return_value=None):
        with TestClient(app) as c:
            r = c.post(
                "/profiles/search",
                json={
                    "industry": "SaaS",
                    "job_title": "Product Manager",
                    "location": "San Francisco",
                    "page": 1,
                    "limit": 10,
                },
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["total_found"] >= 1
            assert any(p["source_platform"] == "LinkedIn" for p in body["results"])