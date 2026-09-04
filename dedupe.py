"""The memory that stops the agent from mailing you the same launch twice.

Rule: same company + same product/feature = duplicate.
Same company + different product/feature = allowed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from .config import CONFIG, REGISTRY_PATH

# Words that carry no disambiguating signal in product names.
_NOISE = {
    "ai", "new", "the", "a", "an", "for", "with", "and", "of", "in", "on",
    "app", "beta", "preview", "public", "general", "availability", "ga",
    "update", "feature", "launch", "release", "version", "v1", "v2", "v3",
    "now", "introducing", "support", "mode", "powered",
}


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)


def normalize(text: str) -> str:
    tokens = [t for t in slugify(text).split("-") if t and t not in _NOISE]
    return " ".join(sorted(set(tokens))) or slugify(text)


def make_key(company: str, product: str) -> str:
    return f"{slugify(company)}::{normalize(product)}".replace(" ", "-")


@dataclass
class Entry:
    key: str
    company: str
    product_name: str
    launch_date: str
    analyzed_on: str
    report_path: str
    one_liner: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Entry":
        return cls(
            key=d["key"],
            company=d.get("company", ""),
            product_name=d.get("product_name", ""),
            launch_date=d.get("launch_date", ""),
            analyzed_on=d.get("analyzed_on", ""),
            report_path=d.get("report_path", ""),
            one_liner=d.get("one_liner", ""),
        )


class Registry:
    def __init__(self, path: Path = REGISTRY_PATH):
        self.path = path
        self.entries: list[Entry] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text() or "{}")
        self.entries = [Entry.from_dict(e) for e in raw.get("entries", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "count": len(self.entries),
            "entries": [e.__dict__ for e in self.entries],
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n")

    # --- dedupe ---------------------------------------------------------

    def is_duplicate(self, company: str, product: str) -> tuple[bool, str | None]:
        key = make_key(company, product)
        for entry in self.entries:
            if entry.key == key:
                return True, entry.product_name

        company_slug = slugify(company)
        target = normalize(product)
        for entry in self.entries:
            if not entry.key.startswith(f"{company_slug}::"):
                continue
            prior = normalize(entry.product_name)
            ratio = SequenceMatcher(None, target, prior).ratio()
            if ratio >= CONFIG.dedupe_threshold:
                return True, entry.product_name
            # Strict containment (e.g. "Copilot Workspace" vs "Copilot Workspace GA")
            t_set, p_set = set(target.split()), set(prior.split())
            if t_set and p_set and (t_set <= p_set or p_set <= t_set):
                return True, entry.product_name
        return False, None

    def add(self, entry: Entry) -> None:
        self.entries.append(entry)

    def recent(self, n: int = 40) -> list[Entry]:
        return sorted(self.entries, key=lambda e: e.analyzed_on, reverse=True)[:n]

    def exclusion_lines(self, limit: int = 120) -> Iterable[str]:
        for e in self.recent(limit):
            yield f"- {e.company} — {e.product_name} (covered {e.analyzed_on})"
