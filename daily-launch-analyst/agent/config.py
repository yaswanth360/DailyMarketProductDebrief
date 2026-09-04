"""Runtime configuration, loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
REGISTRY_PATH = DATA_DIR / "registry.json"
COMPANIES_PATH = DATA_DIR / "companies.yaml"


def _env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name, default)
    if isinstance(val, str):
        val = val.strip()
    return val or None


def _int(name: str, default: int) -> int:
    raw = _env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


@dataclass
class Config:
    anthropic_api_key: str | None = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))

    # Model routing: discovery is search-heavy and cheap, analysis is reasoning-heavy.
    discovery_model: str = field(default_factory=lambda: _env("DISCOVERY_MODEL", "claude-sonnet-5"))
    analysis_model: str = field(default_factory=lambda: _env("ANALYSIS_MODEL", "claude-sonnet-5"))

    lookback_days: int = field(default_factory=lambda: _int("LOOKBACK_DAYS", 7))
    candidates_wanted: int = field(default_factory=lambda: _int("CANDIDATES_WANTED", 10))
    max_search_uses: int = field(default_factory=lambda: _int("MAX_SEARCH_USES", 12))
    dedupe_threshold: float = field(
        default_factory=lambda: float(_env("DEDUPE_THRESHOLD", "0.86"))
    )

    # Email delivery. Pick ONE: Resend (recommended) or SMTP.
    email_to: str | None = field(default_factory=lambda: _env("EMAIL_TO"))
    email_from: str | None = field(default_factory=lambda: _env("EMAIL_FROM"))
    resend_api_key: str | None = field(default_factory=lambda: _env("RESEND_API_KEY"))
    smtp_host: str | None = field(default_factory=lambda: _env("SMTP_HOST"))
    smtp_port: int = field(default_factory=lambda: _int("SMTP_PORT", 587))
    smtp_user: str | None = field(default_factory=lambda: _env("SMTP_USER"))
    smtp_password: str | None = field(default_factory=lambda: _env("SMTP_PASSWORD"))

    def validate(self, require_email: bool = True) -> None:
        if not self.anthropic_api_key:
            raise SystemExit("ANTHROPIC_API_KEY is not set.")
        if require_email:
            if not self.email_to:
                raise SystemExit("EMAIL_TO is not set.")
            if not self.resend_api_key and not (self.smtp_host and self.smtp_user):
                raise SystemExit(
                    "No email transport configured. Set RESEND_API_KEY, or SMTP_HOST/SMTP_USER/SMTP_PASSWORD."
                )


CONFIG = Config()
