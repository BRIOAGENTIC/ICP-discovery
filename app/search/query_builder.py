"""Build multiple search queries from ICP criteria for Tavily."""
from typing import List

from app.models import ICPSearchRequest


def build_queries(req: ICPSearchRequest) -> List[str]:
    """Return a list of distinct natural-language search queries."""
    title = req.job_title.strip()
    industry = req.industry.strip()
    location = req.location.strip() if req.location else ""
    keywords = " ".join(k.strip() for k in req.keywords) if req.keywords else ""

    queries: List[str] = []

    # 1. LinkedIn profiles
    q1 = f"{title} {industry} {location} LinkedIn profile".strip()
    queries.append(q1)

    # 2. X / Twitter
    q2 = f"{title} {industry} {location} Twitter X profile".strip()
    queries.append(q2)

    # 3. Company team pages
    q3 = f"{title} {industry} team about page".strip()
    queries.append(q3)

    # 4. Open-web broad search (personal sites, directories, blogs, forums)
    q4 = f"{title} {industry} {location} {keywords}".strip()
    queries.append(q4)

    # 5. Crunchbase / AngelList / directories
    q5 = f"{title} {industry} founder Crunchbase AngelList Wellfound".strip()
    queries.append(q5)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique
