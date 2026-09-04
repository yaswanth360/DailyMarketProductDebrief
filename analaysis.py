"""Stage 2: deep PM analysis of a single launch."""
from __future__ import annotations

from .config import CONFIG
from .llm import call_structured
from .models import Analysis, Candidate

SYSTEM = """You are a principal product manager writing a daily launch teardown for another
senior PM. You research with web search, then reason like an operator, not a journalist.

Standards you hold yourself to:
- Every number is either sourced or explicitly labelled as an estimate with the math shown.
  Say "~180M MAU (company disclosed, Q2 FY26 earnings)" or "~4M orgs (est: 20M devs / avg 5-seat team)".
  Never state a figure with false precision and never invent a source.
- Segment sizing must be about the addressable users of THIS feature, not the company's total users.
- Revenue sizing is bottom-up: reachable users x realistic attach rate x price point. Show the arithmetic.
- Competitor analysis names actual shipping products, not categories.
- The north star metric must be the one metric that captures delivered customer value for this
  specific feature. Not revenue, not DAU of the parent app. Make it measurable and specific.
- Counter metrics must be the things that get worse if the team over-optimizes the north star.
- If evidence is thin, say so in confidence_notes rather than padding with generic filler.
Write in tight, concrete prose. No marketing language, no hedging boilerplate.
"""

PROMPT = """Analyze this launch in full.

Company: {company}
Product/feature: {product}
Announced: {launch_date}
Initial summary: {one_liner}
Known sources:
{sources}

First, search the web to verify the announcement and gather detail: the official announcement,
pricing or packaging, availability/tiers, any disclosed usage numbers, analyst or press reaction,
and what the closest competitors currently ship. Also search for the competitors' equivalent
features so the comparison is current.

Then produce the complete teardown covering:
1. What actually shipped — concrete capabilities, not the tagline. Include how it works.
2. Who it benefits — specific customer segments, each sized in users/orgs with the basis stated.
3. Revenue opportunity — monetization model and a bottom-up annualized range with the math.
4. The customer pain point it solves, with evidence it was a real pain, plus jobs-to-be-done.
5. Competitors — named shipping products, and whether this launch is ahead / parity / behind each.
6. Competitive verdict — leapfrog, parity, catch-up or defensive, and how durable the edge is.
7. North star metric — one metric, defined precisely, with the rationale.
8. Tracking metrics — 5-8 metrics the team would actually put on the dashboard, defined.
9. Counter metrics — 3-5 guardrails, each with what it guards against and a rough alarm threshold.
10. Strategic read (why now, what it signals) and the key risks.

Populate source_urls with the real URLs you used.
"""


def analyze(candidate: Candidate) -> Analysis:
    sources = "\n".join(f"- {u}" for u in candidate.source_urls) or "- (find them)"
    return call_structured(
        Analysis,
        model=CONFIG.analysis_model,
        system=SYSTEM,
        prompt=PROMPT.format(
            company=candidate.company,
            product=candidate.product_name,
            launch_date=candidate.launch_date,
            one_liner=candidate.one_liner or candidate.why_notable,
            sources=sources,
        ),
        max_tokens=16000,
        web_search=True,
    )
