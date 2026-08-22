"""Build multiple Google CSE queries from ICP criteria."""
from typing import List, Optional

from app.models import ICPSearchRequest


def _quote(s: str) -> str:
    s = s.strip()
    return f'"{s}"' if " " in s else s


def build_queries(req: ICPSearchRequest) -> List[str]:
    """Return a list of distinct search queries that fan out across
    platforms and the open web."""
    title_q = _quote(req.job_title)
    industry_q = _quote(req.industry)
    loc_q = _quote(req.location) if req.location else None
    size_q = _quote(req.company_size) if req.company_size else None
    kw_q = " ".join(_quote(k) for k in req.keywords) if req.keywords else ""

    base_parts = [title_q, industry_q]
    if loc_q:
        base_parts.append(loc_q)
    if size_q:
        base_parts.append(size_q)
    if kw_q:
        base_parts.append(kw_q)
    base = " ".join(p for p in base_parts if p)

    queries: List[str] = []

    # 1. LinkedIn profiles
    q1 = f"site:linkedin.com/in {base}"
    queries.append(q1)

    # 2. X / Twitter
    q2 = f"site:twitter.com OR site:x.com {base}"
    queries.append(q2)

    # 3. Company team pages
    q3 = f'{base} "team" "about"'
    queries.append(q3)

    # 4. Open-web broad search (personal sites, directories, blogs, forums)
    queries.append(base)

    # 5. Crunchbase / AngelList / directories
    q5 = (
        f'site:crunchbase.com OR site:angel.co OR site:wellfound.com '
        f'OR site:apollo.io {base}'
    )
    queries.append(q5)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique