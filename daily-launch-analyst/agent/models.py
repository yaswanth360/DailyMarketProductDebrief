"""Typed schemas. These double as the contract we hand to the model."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    company: str
    product_name: str = Field(description="Specific feature/product name, not the company's whole platform")
    launch_date: str = Field(description="ISO date YYYY-MM-DD of the announcement")
    category: str = ""
    one_liner: str = ""
    source_urls: List[str] = Field(default_factory=list)
    why_notable: str = ""

    def key(self) -> str:
        from .dedupe import make_key

        return make_key(self.company, self.product_name)


class CandidateList(BaseModel):
    candidates: List[Candidate] = Field(default_factory=list)


class Segment(BaseModel):
    segment: str
    description: str = ""
    estimated_users: str = Field("", description="Number of users/orgs, with unit, e.g. '~2.5M developers'")
    sizing_basis: str = Field("", description="How the number was derived: disclosed figure, analyst est., bottom-up")
    confidence: Literal["high", "medium", "low"] = "medium"


class MarketSize(BaseModel):
    monetization_model: str = ""
    revenue_opportunity: str = Field("", description="Annualized $ opportunity with a range")
    sizing_walkthrough: str = Field("", description="Explicit bottom-up math: users x attach rate x ARPU")
    assumptions: List[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"


class Competitor(BaseModel):
    company: str
    product: str = ""
    positioning: str = ""
    gap_or_parity: Literal["ahead", "parity", "behind", "unclear"] = "unclear"
    notes: str = ""


class CompetitiveVerdict(BaseModel):
    stance: Literal["leapfrog", "parity", "catch-up", "defensive"] = "parity"
    rationale: str = ""
    moat_durability: str = Field("", description="How long before this is copied")


class Metric(BaseModel):
    metric: str
    definition: str = ""
    why_it_matters: str = ""


class CounterMetric(BaseModel):
    metric: str
    guards_against: str = ""
    threshold: str = Field("", description="Rough line where the team should worry")


class NorthStar(BaseModel):
    metric: str
    definition: str = ""
    rationale: str = ""


class Analysis(BaseModel):
    company: str
    product_name: str
    launch_date: str
    category: str = ""
    one_liner: str = ""
    source_urls: List[str] = Field(default_factory=list)

    what_launched: List[str] = Field(default_factory=list, description="Concrete capability bullets")
    how_it_works: str = ""

    customer_segments: List[Segment] = Field(default_factory=list)
    segment_size_summary: str = ""

    market_size: Optional[MarketSize] = None

    pain_point: str = ""
    pain_point_evidence: str = ""
    jobs_to_be_done: List[str] = Field(default_factory=list)

    competitors: List[Competitor] = Field(default_factory=list)
    competitive_verdict: Optional[CompetitiveVerdict] = None

    north_star_metric: Optional[NorthStar] = None
    tracking_metrics: List[Metric] = Field(default_factory=list)
    counter_metrics: List[CounterMetric] = Field(default_factory=list)

    strategic_read: str = Field("", description="Why now, and what it signals about the roadmap")
    risks: List[str] = Field(default_factory=list)
    confidence_notes: str = ""

    def slug(self) -> str:
        from .dedupe import slugify

        return f"{slugify(self.company)}-{slugify(self.product_name)}"
