"""Run with: python -m tests.test_dedupe"""
from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

from agent.dedupe import Entry, Registry, make_key
from agent.models import Analysis, CompetitiveVerdict, NorthStar, Segment
from agent.render import to_email_html, to_markdown


def _registry() -> Registry:
    tmp = Path(tempfile.mkdtemp()) / "registry.json"
    reg = Registry(tmp)
    reg.add(
        Entry(
            key=make_key("OpenAI", "Deep Research"),
            company="OpenAI",
            product_name="Deep Research",
            launch_date="2026-08-20",
            analyzed_on="2026-08-21",
            report_path="reports/x.md",
        )
    )
    return reg


def test_dedupe():
    reg = _registry()

    # Exact repeat -> duplicate
    assert reg.is_duplicate("OpenAI", "Deep Research")[0]
    # Cosmetic variation -> duplicate
    assert reg.is_duplicate("OpenAI", "Deep Research (now GA)")[0]
    assert reg.is_duplicate("openai", "deep-research")[0]
    # Different feature, same company -> allowed
    assert not reg.is_duplicate("OpenAI", "Realtime Voice API")[0]
    # Same feature name, different company -> allowed
    assert not reg.is_duplicate("Perplexity", "Deep Research")[0]
    print("dedupe: ok")


def test_render():
    a = Analysis(
        company="Acme",
        product_name="Widget Copilot",
        launch_date="2026-09-01",
        one_liner="An assistant for widget config.",
        what_launched=["Natural-language widget setup", "Rollback of any change"],
        customer_segments=[
            Segment(segment="Ops admins", estimated_users="~120k", sizing_basis="bottom-up", confidence="medium")
        ],
        pain_point="Manual config takes hours.",
        north_star_metric=NorthStar(metric="Weekly configs completed via Copilot"),
        competitive_verdict=CompetitiveVerdict(stance="parity", rationale="Matches Beta Inc."),
    )
    md = to_markdown(a, date(2026, 9, 3))
    html = to_email_html(a, date(2026, 9, 3), "https://example.com")
    assert "Widget Copilot" in md and "North star" in md
    assert "<html" in html and "Widget Copilot" in html
    print("render: ok")


if __name__ == "__main__":
    test_dedupe()
    test_render()
    print("all tests passed")
