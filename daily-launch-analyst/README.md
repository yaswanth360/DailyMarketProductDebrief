# Daily Launch Analyst

An autonomous agent that finds one notable product/feature launch from the last 7 days,
tears it down the way a senior PM would, emails it to you every morning, and archives
every teardown in this repo — never repeating the same feature from the same company.

```
cron 13:00 UTC
   │
   ├─ 1. DISCOVERY   Claude + web search → ~10 candidate launches (last 7 days)
   ├─ 2. DEDUPE      registry.json filter → first company+feature never covered
   ├─ 3. ANALYSIS    Claude + web search → full structured teardown (validated JSON)
   ├─ 4. ARCHIVE     reports/YYYY/MM/*.md + registry entry + index, committed to git
   └─ 5. DELIVER     responsive HTML email (Resend or SMTP)
```

## What each teardown contains

| # | Section | Detail |
|---|---|---|
| 1 | What launched | Concrete capabilities and how it works |
| 2 | Who it benefits | Named segments, each sized in users/orgs with sizing basis + confidence |
| 3 | Revenue opportunity | Monetization model, annualized range, bottom-up math, assumptions |
| 4 | Pain point | The problem, evidence it was real, jobs-to-be-done |
| 5 | Competitors | Named shipping products, ahead/parity/behind per rival |
| 6 | Competitive verdict | leapfrog / parity / catch-up / defensive + moat durability |
| 7 | North star metric | One metric, defined, with rationale |
| 8 | Tracking metrics | 5–8 dashboard metrics with definitions |
| 9 | Counter metrics | 3–5 guardrails with alarm thresholds |
| 10 | Strategic read + risks | Why now, what it signals, what could go wrong |

## Setup (about 10 minutes)

**1. Create the repo**

```bash
git init && git add . && git commit -m "init: daily launch analyst"
gh repo create daily-launch-analyst --private --source=. --push
```

**2. Add secrets** — repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | from console.anthropic.com |
| `EMAIL_TO` | yes | your address; comma-separate for several |
| `RESEND_API_KEY` | one of | resend.com — free tier, simplest path |
| `EMAIL_FROM` | with Resend | verified sender, or `onboarding@resend.dev` to start |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | one of | Gmail needs an App Password, not your login |

Optional repo *variables*: `DISCOVERY_MODEL`, `ANALYSIS_MODEL`, `LOOKBACK_DAYS`.

**3. Test it** — Actions tab → Daily Launch Analysis → Run workflow. Tick *dry run*
for the first pass to see the analysis without sending mail or writing the registry.

**4. Adjust the send time** — edit the cron in `.github/workflows/daily-launch-analysis.yml`.
It's UTC, so `0 13 * * *` is 6am Pacific. GitHub's scheduler often lags 5–20 minutes.

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill it in
set -a && source .env && set +a

python -m agent.main --dry-run   # analyze + print, no email, no registry write
python -m agent.main --no-email  # archive only
python -m agent.main             # full run
python -m tests.test_dedupe      # tests
```

## How the no-repeats rule works

`data/registry.json` is the agent's memory. Each entry gets a key of
`company-slug::normalized-product`, where normalization lowercases, strips
punctuation, and drops noise tokens (`ai`, `new`, `beta`, `GA`, `update`, `introducing`…).

A candidate is rejected if, **for the same company**, it matches an existing entry by:
- identical key, or
- fuzzy similarity ≥ `DEDUPE_THRESHOLD` (default 0.86), or
- token containment — so "Copilot Workspace" and "Copilot Workspace now GA" collide.

Different feature, same company → allowed. Same feature name, different company → allowed.
The check runs twice: once on the discovery candidate, and again after analysis in case
the analyst corrected the product's official name.

The exclusion list is also fed into the discovery prompt, so the model avoids re-suggesting
covered launches in the first place — the registry check is the backstop, not the only line.

## Tuning it

- **`data/companies.yaml`** — the watchlist. Edit freely; it's read fresh each run.
  Add your own competitive set, drop the ones you don't care about.
- **`agent/analysis.py`** — the `SYSTEM` prompt holds the analytical standards
  (sourced numbers, bottom-up sizing, no false precision). Sharpen it to taste.
- **`agent/models.py`** — the schema *is* the spec. Add a field there and it
  automatically flows into the prompt, the markdown, and the validator.
- **Multiple launches per day** — loop `pick_candidate` in `agent/main.py` over N picks
  and send a digest. The registry handles the rest unchanged.

## Cost

Two API calls a day, both with web search — roughly $0.15–0.50 per run depending on
how many searches the model runs, so on the order of $5–15/month. `MAX_SEARCH_USES`
caps the search count. GitHub Actions time is free on public repos and well within the
free minutes on private ones.

## A caution on the numbers

Segment sizes and revenue estimates are model-derived and explicitly labelled with their
basis and a confidence level. Treat them as a starting hypothesis with the math shown,
not as a citable figure. The `confidence_notes` field flags where evidence was thin.
