"""Turn an Analysis into (a) a markdown report for the repo and (b) an HTML email."""
from __future__ import annotations

import html
from datetime import date

from .models import Analysis

_STANCE_COLOR = {
    "leapfrog": "#0f7b3e",
    "parity": "#8a6d00",
    "catch-up": "#a83232",
    "defensive": "#5b4bb5",
}


# --------------------------------------------------------------------------
# Markdown (archived in the repo)
# --------------------------------------------------------------------------

def to_markdown(a: Analysis, run_date: date) -> str:
    L: list[str] = []
    add = L.append

    add("---")
    add(f'company: "{a.company}"')
    add(f'product: "{a.product_name}"')
    add(f"launch_date: {a.launch_date}")
    add(f"analyzed_on: {run_date.isoformat()}")
    add(f'category: "{a.category}"')
    add("---\n")

    add(f"# {a.company} — {a.product_name}\n")
    if a.one_liner:
        add(f"> {a.one_liner}\n")
    add(f"**Announced:** {a.launch_date}  |  **Analyzed:** {run_date.isoformat()}\n")

    add("## 1. What launched\n")
    for b in a.what_launched:
        add(f"- {b}")
    if a.how_it_works:
        add(f"\n**How it works.** {a.how_it_works}")
    add("")

    add("## 2. Who it benefits\n")
    if a.customer_segments:
        add("| Segment | Size | Basis | Confidence |")
        add("|---|---|---|---|")
        for s in a.customer_segments:
            add(f"| {s.segment} | {s.estimated_users or '—'} | {s.sizing_basis or '—'} | {s.confidence} |")
        add("")
        for s in a.customer_segments:
            if s.description:
                add(f"- **{s.segment}** — {s.description}")
    if a.segment_size_summary:
        add(f"\n{a.segment_size_summary}")
    add("")

    add("## 3. Revenue opportunity\n")
    if a.market_size:
        m = a.market_size
        add(f"- **Monetization:** {m.monetization_model or '—'}")
        add(f"- **Opportunity:** {m.revenue_opportunity or '—'}  _(confidence: {m.confidence})_")
        if m.sizing_walkthrough:
            add(f"\n**Math.** {m.sizing_walkthrough}")
        if m.assumptions:
            add("\n**Assumptions**")
            for x in m.assumptions:
                add(f"- {x}")
    add("")

    add("## 4. Customer pain point\n")
    add(a.pain_point or "—")
    if a.pain_point_evidence:
        add(f"\n**Evidence.** {a.pain_point_evidence}")
    if a.jobs_to_be_done:
        add("\n**Jobs to be done**")
        for j in a.jobs_to_be_done:
            add(f"- {j}")
    add("")

    add("## 5. Competitive landscape\n")
    if a.competitors:
        add("| Competitor | Product | Positioning | vs. this launch |")
        add("|---|---|---|---|")
        for c in a.competitors:
            add(f"| {c.company} | {c.product or '—'} | {c.positioning or '—'} | {c.gap_or_parity} |")
        add("")
        for c in a.competitors:
            if c.notes:
                add(f"- **{c.company}** — {c.notes}")
    if a.competitive_verdict:
        v = a.competitive_verdict
        add(f"\n**Verdict: {v.stance.upper()}.** {v.rationale}")
        if v.moat_durability:
            add(f"\n**Durability.** {v.moat_durability}")
    add("")

    add("## 6. North star metric\n")
    if a.north_star_metric:
        n = a.north_star_metric
        add(f"**{n.metric}**\n")
        if n.definition:
            add(f"- _Definition:_ {n.definition}")
        if n.rationale:
            add(f"- _Why:_ {n.rationale}")
    add("")

    add("## 7. Tracking metrics\n")
    if a.tracking_metrics:
        add("| Metric | Definition | Why it matters |")
        add("|---|---|---|")
        for m in a.tracking_metrics:
            add(f"| {m.metric} | {m.definition or '—'} | {m.why_it_matters or '—'} |")
    add("")

    add("## 8. Counter metrics\n")
    if a.counter_metrics:
        add("| Counter metric | Guards against | Alarm threshold |")
        add("|---|---|---|")
        for m in a.counter_metrics:
            add(f"| {m.metric} | {m.guards_against or '—'} | {m.threshold or '—'} |")
    add("")

    if a.strategic_read:
        add("## 9. Strategic read\n")
        add(a.strategic_read + "\n")

    if a.risks:
        add("## 10. Risks\n")
        for r in a.risks:
            add(f"- {r}")
        add("")

    if a.confidence_notes:
        add("## Confidence notes\n")
        add(a.confidence_notes + "\n")

    if a.source_urls:
        add("## Sources\n")
        for u in a.source_urls:
            add(f"- {u}")
        add("")

    return "\n".join(L)


# --------------------------------------------------------------------------
# HTML email
# --------------------------------------------------------------------------

def _e(text: str) -> str:
    return html.escape(text or "")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    th = "".join(
        f'<th style="text-align:left;padding:8px 10px;border-bottom:2px solid #e3e3e0;'
        f'font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#6b6b66;">{_e(h)}</th>'
        for h in headers
    )
    tr = ""
    for row in rows:
        tds = "".join(
            f'<td style="padding:9px 10px;border-bottom:1px solid #eeeeec;'
            f'font-size:14px;vertical-align:top;color:#282824;">{_e(c)}</td>'
            for c in row
        )
        tr += f"<tr>{tds}</tr>"
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;margin:10px 0 18px;"><thead><tr>{th}</tr></thead>'
        f"<tbody>{tr}</tbody></table>"
    )


def _section(n: int, title: str, body: str) -> str:
    if not body.strip():
        return ""
    return (
        f'<h2 style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;'
        f'color:#9a9a94;margin:30px 0 8px;font-weight:600;">{n:02d} — {_e(title)}</h2>{body}'
    )


def _bullets(items: list[str]) -> str:
    if not items:
        return ""
    lis = "".join(
        f'<li style="margin:0 0 7px;font-size:15px;line-height:1.55;color:#282824;">{_e(i)}</li>'
        for i in items
    )
    return f'<ul style="padding-left:20px;margin:6px 0 0;">{lis}</ul>'


def _p(text: str) -> str:
    if not text:
        return ""
    return f'<p style="font-size:15px;line-height:1.6;color:#282824;margin:6px 0;">{_e(text)}</p>'


def to_email_html(a: Analysis, run_date: date, repo_url: str | None = None) -> str:
    v = a.competitive_verdict
    stance_html = ""
    if v:
        color = _STANCE_COLOR.get(v.stance, "#5b5b55")
        stance_html = (
            f'<span style="display:inline-block;padding:3px 10px;border-radius:100px;'
            f'background:{color}1a;color:{color};font-size:12px;font-weight:600;'
            f'letter-spacing:.04em;text-transform:uppercase;">{_e(v.stance)}</span>'
        )

    seg_rows = [
        [s.segment, s.estimated_users or "—", s.sizing_basis or "—", s.confidence]
        for s in a.customer_segments
    ]
    comp_rows = [
        [c.company, c.product or "—", c.positioning or "—", c.gap_or_parity]
        for c in a.competitors
    ]
    track_rows = [[m.metric, m.definition or "—"] for m in a.tracking_metrics]
    counter_rows = [
        [m.metric, m.guards_against or "—", m.threshold or "—"] for m in a.counter_metrics
    ]

    market = ""
    if a.market_size:
        m = a.market_size
        market = (
            _p(f"Monetization: {m.monetization_model}")
            + f'<p style="font-size:22px;font-weight:600;color:#1a1a17;margin:10px 0 4px;">{_e(m.revenue_opportunity)}</p>'
            + _p(m.sizing_walkthrough)
            + _bullets(m.assumptions)
        )

    ns = ""
    if a.north_star_metric:
        n = a.north_star_metric
        ns = (
            '<div style="border-left:3px solid #c4623d;padding:2px 0 2px 16px;margin:10px 0;">'
            f'<p style="font-size:18px;font-weight:600;color:#1a1a17;margin:0 0 6px;">{_e(n.metric)}</p>'
            + _p(n.definition)
            + _p(n.rationale)
            + "</div>"
        )

    verdict = ""
    if v:
        verdict = stance_html + _p(v.rationale) + _p(v.moat_durability)

    sources = ""
    if a.source_urls:
        links = "".join(
            f'<li style="margin:0 0 5px;font-size:13px;word-break:break-all;">'
            f'<a href="{_e(u)}" style="color:#7a6f5f;">{_e(u)}</a></li>'
            for u in a.source_urls
        )
        sources = f'<ul style="padding-left:20px;margin:6px 0;">{links}</ul>'

    footer_link = (
        f'<p style="font-size:12px;color:#9a9a94;margin:0;">Full archive: '
        f'<a href="{_e(repo_url)}" style="color:#9a9a94;">{_e(repo_url)}</a></p>'
        if repo_url
        else ""
    )

    body = "".join(
        [
            _section(1, "What launched", _bullets(a.what_launched) + _p(a.how_it_works)),
            _section(
                2,
                "Who it benefits",
                _table(["Segment", "Size", "Basis", "Conf."], seg_rows)
                + _bullets([f"{s.segment}: {s.description}" for s in a.customer_segments if s.description])
                + _p(a.segment_size_summary),
            ),
            _section(3, "Revenue opportunity", market),
            _section(
                4,
                "Pain point",
                _p(a.pain_point) + _p(a.pain_point_evidence) + _bullets(a.jobs_to_be_done),
            ),
            _section(
                5,
                "Competitive landscape",
                _table(["Competitor", "Product", "Positioning", "vs. launch"], comp_rows) + verdict,
            ),
            _section(6, "North star metric", ns),
            _section(7, "Tracking metrics", _table(["Metric", "Definition"], track_rows)),
            _section(
                8,
                "Counter metrics",
                _table(["Counter metric", "Guards against", "Threshold"], counter_rows),
            ),
            _section(9, "Strategic read", _p(a.strategic_read)),
            _section(10, "Risks", _bullets(a.risks)),
            _section(11, "Confidence notes", _p(a.confidence_notes)),
            _section(12, "Sources", sources),
        ]
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(a.company)} — {_e(a.product_name)}</title></head>
<body style="margin:0;padding:0;background:#faf9f7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#faf9f7;padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:660px;background:#ffffff;border:1px solid #ecebe7;border-radius:12px;padding:34px 34px 26px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<tr><td>
  <p style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#9a9a94;margin:0 0 14px;">
    Daily Launch Teardown · {_e(run_date.strftime('%A, %d %B %Y'))}
  </p>
  <h1 style="font-size:27px;line-height:1.25;color:#1a1a17;margin:0 0 6px;font-weight:600;">
    {_e(a.company)} — {_e(a.product_name)}
  </h1>
  <p style="font-size:16px;line-height:1.5;color:#5b5b55;margin:0 0 12px;">{_e(a.one_liner)}</p>
  <p style="font-size:13px;color:#9a9a94;margin:0 0 4px;">
    Announced {_e(a.launch_date)}{' · ' + _e(a.category) if a.category else ''}
  </p>
  {body}
  <hr style="border:none;border-top:1px solid #ecebe7;margin:34px 0 14px;">
  <p style="font-size:12px;color:#9a9a94;margin:0 0 4px;">
    Generated by your launch-analyst agent. Figures marked as estimates are model-derived — verify before citing.
  </p>
  {footer_link}
</td></tr></table>
</td></tr></table>
</body></html>"""


def to_email_text(a: Analysis, run_date: date) -> str:
    return to_markdown(a, run_date)


def subject_line(a: Analysis, run_date: date) -> str:
    return f"[{run_date.strftime('%b %d')}] {a.company}: {a.product_name}"
