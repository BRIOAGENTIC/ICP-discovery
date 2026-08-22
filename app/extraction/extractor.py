"""Extract structured profile fields from title/snippet/url."""
import re
from typing import List, Optional, Tuple 
from urllib.parse import urlparse

from app.models import ICPSearchRequest


# ---------- Platform detection ----------
PLATFORM_RULES = [
    ("linkedin.com", "LinkedIn"),
    ("twitter.com", "X (Twitter)"),
    ("x.com", "X (Twitter)"),
    ("github.com", "GitHub"),
    ("crunchbase.com", "Crunchbase"),
    ("angel.co", "AngelList"),
    ("wellfound.com", "Wellfound"),
    ("apollo.io", "Apollo"),
    ("medium.com", "Medium"),
    ("substack.com", "Substack"),
    ("about.me", "about.me"),
    ("behance.net", "Behance"),
    ("dribbble.com", "Dribbble"),
    ("youtube.com", "YouTube"),
    ("reddit.com", "Reddit"),
]


def detect_platform(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for fragment, label in PLATFORM_RULES:
        if fragment in host:
            return label
    # Heuristic: if path contains /team or /about -> company page
    path = (urlparse(url).path or "").lower()
    if any(seg in path for seg in ("/team", "/about", "/people", "/leadership")):
        return "company page"
    return "personal website / directory"


# ---------- Name extraction ----------
# LinkedIn pattern: "Jane Doe - Senior PM at Acme | LinkedIn"
_LINKEDIN_NAME = re.compile(r"^([^|–\-]+?)\s*[-–|]\s*[^|]*at\s", re.IGNORECASE)
# Generic: "Jane Doe — Senior PM @ Acme"
_GENERIC_NAME = re.compile(r"^([A-Z][a-zA-Z'\-]+\s+[A-Z][a-zA-Z'\-]+)\s*[-–|—]")
# X/Twitter pattern: "@handle (Display Name)"
_X_NAME = re.compile(r"\(([A-Z][a-zA-Z'\-]+\s+[A-Z][a-zA-Z'\-]+)\)")


def extract_name(title: str, snippet: str, platform: str) -> Optional[str]:
    text = (title or "").strip()
    if platform == "LinkedIn":
        m = _LINKEDIN_NAME.match(text)
        if m:
            return m.group(1).strip()
    if platform == "X (Twitter)":
        m = _X_NAME.search(text) or _X_NAME.search(snippet or "")
        if m:
            return m.group(1).strip()
    m = _GENERIC_NAME.match(text)
    if m:
        return m.group(1).strip()
    # Try snippet
    m = _GENERIC_NAME.match((snippet or "").strip())
    if m:
        return m.group(1).strip()
    return None


# ---------- Relevance scoring ----------
def _tokenize(s: str) -> List[str]:
    return [t for t in re.split(r"\W+", (s or "").lower()) if t]


def compute_relevance(
    title: str, snippet: str, req: ICPSearchRequest
) -> float:
    hay = f"{title} {snippet}".lower()
    score = 0.0
    max_score = 0.0

    def add(weight: float, present: bool) -> None:
        nonlocal score, max_score
        max_score += weight
        if present:
            score += weight

    add(30.0, req.job_title.lower() in hay)
    add(25.0, req.industry.lower() in hay)
    if req.location:
        add(20.0, req.location.lower() in hay)
    if req.company_size:
        # Allow loose numeric match (e.g. "51-200" -> check "51" or "200")
        size = req.company_size.lower()
        add(15.0, size in hay or any(
            tok in hay for tok in _tokenize(size) if len(tok) >= 2
        ))
    if req.keywords:
        for kw in req.keywords:
            add(10.0, kw.lower() in hay)

    if max_score == 0:
        return 0.0
    return round((score / max_score) * 100.0, 2)


def extract_role_company(snippet: str) -> Optional[str]:
    """Try to extract 'Role at Company' style text from snippet."""
    if not snippet:
        return None
    m = re.search(
        r"([A-Z][\w\s]{2,40}?)\s+at\s+([A-Z][\w&\s.,']{1,40})",
        snippet,
    )
    if m:
        return m.group(0).strip()
    return None
