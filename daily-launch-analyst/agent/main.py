"""Orchestrator: discover -> dedupe -> analyze -> archive -> email."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from .analysis import analyze
from .archive import record, write_index, write_report
from .config import CONFIG
from .dedupe import Registry
from .discovery import find_candidates, pick_candidate
from .render import subject_line, to_email_html, to_email_text


def run(dry_run: bool = False, no_email: bool = False) -> int:
    CONFIG.validate(require_email=not (dry_run or no_email))
    run_date = date.today()
    registry = Registry()

    print(f"[1/5] Discovering launches from the last {CONFIG.lookback_days} days...")
    candidates = find_candidates(registry)
    print(f"      {len(candidates)} candidate(s) in window.")
    for c in candidates:
        print(f"      · {c.company} — {c.product_name} ({c.launch_date})")

    print("[2/5] Filtering against the coverage registry...")
    chosen, skip_log = pick_candidate(candidates, registry)
    for line in skip_log:
        print(f"      {line}")
    if chosen is None:
        print("      No fresh launch found. Widen LOOKBACK_DAYS or extend data/companies.yaml.")
        _gh_output("status", "no_candidate")
        return 0
    print(f"      Selected: {chosen.company} — {chosen.product_name}")

    print("[3/5] Running deep analysis...")
    analysis = analyze(chosen)

    # The analyst may correct the product name; re-check for duplicates before publishing.
    dup, matched = registry.is_duplicate(analysis.company, analysis.product_name)
    if dup:
        print(f"      Post-analysis duplicate ('{matched}'). Discarding without sending.")
        _gh_output("status", "duplicate_after_analysis")
        return 0

    print("[4/5] Archiving...")
    path = write_report(analysis, run_date)
    print(f"      Wrote {path}")
    if not dry_run:
        record(registry, analysis, run_date, path)
        write_index(registry)
        print("      Registry and index updated.")

    print("[5/5] Sending email...")
    if dry_run or no_email:
        print("      Skipped (dry run).")
    else:
        from .mailer import send

        send(
            subject_line(analysis, run_date),
            to_email_html(analysis, run_date, os.environ.get("REPO_URL")),
            to_email_text(analysis, run_date),
        )

    _gh_output("status", "sent")
    _gh_output("company", analysis.company)
    _gh_output("product", analysis.product_name)
    _gh_output("report_path", str(path))
    print("Done.")
    return 0


def _gh_output(key: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"{key}={value}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily product launch teardown agent")
    ap.add_argument("--dry-run", action="store_true", help="Analyze and print, but do not email or record")
    ap.add_argument("--no-email", action="store_true", help="Archive and record, but skip email")
    args = ap.parse_args()
    try:
        sys.exit(run(dry_run=args.dry_run, no_email=args.no_email))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
