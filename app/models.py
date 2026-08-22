"""Pydantic models for request/response."""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ICPSearchRequest(BaseModel):
    industry: str = Field(..., min_length=1, description="Target industry")
    job_title: str = Field(..., min_length=1, description="Target job title")
    company_size: Optional[str] = Field(
        None, description="e.g. '51-200', 'Startup', 'Enterprise'"
    )
    location: Optional[str] = Field(None, description="Geographic location")
    keywords: Optional[List[str]] = Field(
        None, description="Extra keywords to refine search"
    )

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(20, ge=1, le=100, description="Results per page")

    @field_validator("industry", "job_title")
    @classmethod
    def strip_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class ProfileResult(BaseModel):
    name: Optional[str] = None
    source_platform: str
    profile_url: str
    matched_snippet: str
    relevance_score: float


class ICPSearchResponse(BaseModel):
    page: int
    limit: int
    total_found: int
    results: List[ProfileResult]