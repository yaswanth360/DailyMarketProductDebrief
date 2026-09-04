"""Stage 1: find candidate launches from the last N days."""
from __future__ import annotations

from datetime import date, timedelta

import yaml

from .config import CONFIG, COMPANIES_PATH
from .dedupe import Registry
from .llm import call_structured
from .models import Candidate, CandidateList

SYSTEM = """You are a product-intelligence scout for a senior PM.
You search the web to find genuinely new product and feature launches from major
technology companies and well-funded startups.

Hard rules:
- Only announcements published within the stated date window. Verify the date on the source page.
- A launch means a shipped or formally announced product/feature: GA, public beta, preview,
  or a named capability. NOT: funding rounds, exec hires, earnings, partnerships without a product,
  conference dates, blog think-pieces, or rumours.
- Prefer first-party sources (company newsroom, product blog, changelog, developer docs).
- Never invent a launch. If you cannot find enough qualifying items, return fewer.
"""

PROMPT = """Today is {today}. Find product/feature launches announced between {start} and {today} (inclusive).

Search across these companies and their peers:
{watchlist}

Also include notable launches from well-funded startups in these categories:
{categories}

ALREADY COVERED — do not return these exact products/features again.
A different product or feature from the same company is fine and encouraged:
{exclusions}

Run multiple searches (company newsrooms, "launch"/"introducing"/"now available" queries,
changelogs, and tech press) before answering.

Return the {n} best candidates, ranked by how instructive they are to analyze as a PM case study:
prefer launches with a clear customer segment, a visible competitive response, and enough public
detail to reason about metrics. Set launch_date to the announcement date shown on the source.
"""


def load_watchlist() -> dict:
    if not COMPANIES_PATH.exists():
        return {"companies": [], "categories": []}
    return yaml.safe_load(COMPANIES_PATH.read_text()) or {}


def find_candidates(registry: Registry) -> list[Candidate]:
    watchlist = load_watchlist()
    companies = watchlist.get("companies", [])
    categories = watchlist.get("categories", [])

    today = date.today()
    start = today - timedelta(days=CONFIG.lookback_days)

    exclusions = "\n".join(registry.exclusion_lines()) or "- (nothing covered yet)"

    result = call_structured(
        CandidateList,
        model=CONFIG.discovery_model,
        system=SYSTEM,
        prompt=PROMPT.format(
            today=today.isoformat(),
            start=start.isoformat(),
            watchlist="\n".join(f"- {c}" for c in companies) or "- (any major tech company)",
            categories="\n".join(f"- {c}" for c in categories) or "- (any software category)",
            exclusions=exclusions,
            n=CONFIG.candidates_wanted,
        ),
        max_tokens=8000,
        web_search=True,
    )

    # Belt and braces: enforce the date window locally too.
    kept: list[Candidate] = []
    for c in result.candidates:
        try:
            d = date.fromisoformat(c.launch_date[:10])
        except (ValueError, TypeError):
            kept.append(c)  # keep, but it will be sanity-checked in analysis
            continue
        if start <= d <= today + timedelta(days=1):
            kept.append(c)
    return kept


def pick_candidate(candidates: list[Candidate], registry: Registry) -> tuple[Candidate | None, list[str]]:
    """Return the first non-duplicate candidate, plus a log of what was skipped."""
    log: list[str] = []
    for c in candidates:
        dup, matched = registry.is_duplicate(c.company, c.product_name)
        if dup:
            log.append(f"skipped duplicate: {c.company} — {c.product_name} (matches '{matched}')")
            continue
        return c, log
    return None, log
