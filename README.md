# DailyMarketProductDebrief
Become 1% better PM everyday. Track Latest Product Launches and analyze, understand from a product lens standpoint to stay up-to-date in a busy world. 

# Daily Market Product Debrief

An AI agent that emails you one deep product teardown every morning.

Each day it finds a notable product or feature launch from the past 7 days — from a major
tech company or a well-funded startup — and breaks it down the way a senior PM would:
who it's for, how big that market is, what pain it solves, who it competes with, and what
metrics the team behind it is almost certainly watching. Every teardown is also saved into
this repository so you build a searchable archive over time.

It never sends you the same feature from the same company twice.

**You do not need to know how to code to run this.** The setup below takes about 20 minutes,
happens entirely in your web browser, and costs roughly $5–15/month in API usage.

---

## What lands in your inbox

A formatted email, every morning, containing:

| # | Section | What you get |
|---|---|---|
| 1 | What launched | The actual capabilities, not the marketing tagline |
| 2 | Who it benefits | Named customer segments, each sized in users or organizations |
| 3 | Revenue opportunity | Monetization model plus a bottom-up dollar estimate, with the math shown |
| 4 | Customer pain point | The problem it solves and evidence the problem was real |
| 5 | Competitive landscape | Named rival products, and whether this launch is ahead, at parity, or behind |
| 6 | Competitive verdict | Leapfrog / parity / catch-up / defensive, and how long the edge lasts |
| 7 | North star metric | The single metric this feature is built to move |
| 8 | Tracking metrics | 5–8 metrics that would sit on the team's dashboard |
| 9 | Counter metrics | Guardrails — what breaks if they over-optimize the north star |
| 10 | Strategic read + risks | Why now, what it signals about the roadmap, what could go wrong |

---

## How it works

```
Every morning at 6:00 AM
        │
        ├─ 1. DISCOVER   Searches the web for launches from the last 7 days
        ├─ 2. DE-DUPE    Skips anything already covered in your archive
        ├─ 3. ANALYZE    Researches the winner and writes the full teardown
        ├─ 4. ARCHIVE    Saves it to /reports and commits it to this repo
        └─ 5. EMAIL      Sends it to you
```

Everything runs on GitHub's free servers. Nothing needs to stay on your laptop, and your
computer doesn't need to be switched on.

---

# Setup

Follow these five parts in order. Parts 1–4 are all point-and-click.

## Part 1 — Get an Anthropic API key

This is what powers the agent's research and writing.

1. Go to **[console.anthropic.com](https://console.anthropic.com)** and sign up.
2. Open **Billing** in the left sidebar and add a payment method. Load $10 in credit to start
   — the agent uses roughly $0.15–0.50 per day.
3. Open **API Keys** → **Create Key**. Name it `daily-debrief`.
4. **Copy the key now and paste it somewhere safe.** It starts with `sk-ant-` and Anthropic
   will never show it to you again after you close that dialog.

## Part 2 — Set up email sending

The agent needs a way to send mail. Pick **one** of these two options.

### Option A — Resend (recommended, 5 minutes)

Easiest path. Free for up to 3,000 emails a month, which is far more than you'll use.

1. Go to **[resend.com](https://resend.com)** and sign up.
2. Open **API Keys** → **Create API Key**. Give it **Sending access**.
3. Copy the key (it starts with `re_`) and save it alongside your Anthropic key.
4. You can send from `onboarding@resend.dev` immediately without verifying anything.
   If you'd rather it come from your own domain, add and verify the domain under
   **Domains** — optional, and you can do it later.

### Option B — Gmail

Works fine, but slightly fiddlier because Google requires an App Password.

1. Turn on **2-Step Verification** at
   [myaccount.google.com/security](https://myaccount.google.com/security). App Passwords
   are unavailable without it.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Create a password named `daily-debrief`. Google shows you 16 letters — copy them and
   remove the spaces.
4. This is **not** your Gmail login password. Never use your real password here.

## Part 3 — Get the code into your GitHub repository

### If you already have the code in your repo, skip to Part 4.

<details>
<summary><strong>Upload via the browser (no command line)</strong></summary>

1. Unzip the project folder on your computer. You should see folders named `agent`,
   `data`, `reports`, `tests`, and a hidden `.github` folder.
2. Go to your repository on GitHub and click **Add file** → **Upload files**.
3. Drag the whole folder in. GitHub preserves the folder structure.
4. Click **Commit changes**.

**One catch:** GitHub's web uploader silently skips hidden folders, so `.github` won't make
it. You'll need to create that file by hand:

- Click **Add file** → **Create new file**
- In the filename box type exactly: `.github/workflows/daily-launch-analysis.yml`
  (typing the slashes creates the folders automatically)
- Paste in the contents of the `daily-launch-analysis.yml` file from your unzipped folder
- Click **Commit changes**

</details>

<details>
<summary><strong>Upload via the command line</strong></summary>

```bash
cd path/to/daily-launch-analyst

git init
git add .
git commit -m "init: daily market product debrief agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

When it asks for a password, GitHub wants a Personal Access Token, not your account
password. Create one at **Settings → Developer settings → Personal access tokens →
Fine-grained tokens** with **Contents: read/write** *and* **Workflows: read/write**.
Without the workflows permission the push is rejected, because this project contains a
workflow file.

If the repo already has a README and the push is rejected, run
`git pull origin main --allow-unrelated-histories` first, then push again.

</details>

**Before moving on, confirm your repo contains a folder called `agent` and a file at
`.github/workflows/daily-launch-analysis.yml`.** If either is missing, nothing will run.

## Part 4 — Add your keys to GitHub

Your keys go into GitHub's encrypted secret storage. They're never visible in the code,
in logs, or to anyone who views your repo.

In your repository: **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Add each of these, one at a time:

**Always required:**

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your `sk-ant-...` key from Part 1 |
| `EMAIL_TO` | The address you want the debrief sent to |

**If you chose Resend:**

| Name | Value |
|---|---|
| `RESEND_API_KEY` | Your `re_...` key |
| `EMAIL_FROM` | `onboarding@resend.dev` (or your verified domain address) |

**If you chose Gmail:**

| Name | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | The 16-character App Password, spaces removed |
| `EMAIL_FROM` | Your Gmail address |

Type the names **exactly** as written above, capitals included. A typo here produces a
confusing "not set" error later.

### Then enable write access

Still in Settings: **Actions** → **General** → scroll to **Workflow permissions** →
select **Read and write permissions** → **Save**.

This lets the agent save each teardown back into your repository. Skip it and the job
will fail at the final step every single day.

## Part 5 — Test it

1. Click the **Actions** tab at the top of your repository.
2. If you see a "Workflows aren't being run on this forked repository" banner, click the
   green button to enable them.
3. In the left sidebar click **Daily Launch Analysis**.
4. Click **Run workflow** (right-hand side) → tick **dry run** → **Run workflow**.

Dry run does the full research and analysis but doesn't email you or write to the archive
— it's the safe way to check your setup.

Wait 3–5 minutes, then click into the run and open the **Run agent** step. You should see:

```
[1/5] Discovering launches from the last 7 days...
      3 candidate(s) in window.
      · Anthropic — Claude for Excel
      ...
[3/5] Running deep analysis...
[4/5] Archiving...
[5/5] Sending email...
      Skipped (dry run).
Done.
```

**If that looks right, run it again with dry run unticked.** Check your inbox — and your
spam folder, since it's a first-time sender. Mark it "not spam" so future ones land properly.

You're done. It now runs on its own every morning.

---

# Customizing it

## Change the delivery time

The schedule lives in `.github/workflows/daily-launch-analysis.yml`, on this line:

```yaml
- cron: "0 13 * * *"
```

The time is in **UTC**, always — it does not follow your local time zone or daylight saving.

| You want | Use |
|---|---|
| 6:00 AM US Pacific | `"0 13 * * *"` |
| 6:00 AM US Eastern | `"0 10 * * *"` |
| 7:00 AM UK | `"0 6 * * *"` |
| 8:00 AM India | `"30 2 * * *"` |
| 9:00 AM Central Europe | `"0 7 * * *"` |

Weekdays only? Change the last field from `*` to `1-5`.

GitHub's scheduler is best-effort and often runs 5–20 minutes late when their servers are
busy. That's normal and not something you can tune.

## Change which companies get watched

Edit `data/companies.yaml` directly on GitHub — click the file, then the pencil icon. Add
your competitors, remove sectors you don't care about. The agent re-reads it every run, so
changes take effect the next morning.

## Change what the analysis covers

- `agent/analysis.py` — the instructions that set the analytical standards
- `agent/models.py` — the structure of the teardown itself. Add a field here and it
  automatically appears in both the email and the saved report.

---

# Troubleshooting

**"ANTHROPIC_API_KEY is not set"**
The secret name is misspelled or was added to the wrong repository. Check
Settings → Secrets and variables → Actions, and confirm the name matches exactly.

**The workflow fails on the "Commit archive" step**
You missed the Workflow permissions setting in Part 4. Go back and set it to
**Read and write permissions**.

**No email arrived, but the log says "Email sent"**
Check spam. With Gmail, also confirm you used the App Password rather than your account
password. With Resend, open their dashboard — it logs every send attempt and the reason
for any bounce.

**"No fresh launch found"**
Everything the agent found was already in your archive. Not an error. It'll pick something
new tomorrow. To widen the net, add more companies to `data/companies.yaml`.

**"refusing to allow a token to create or update workflow"**
Your Personal Access Token is missing the **Workflows: read/write** permission. Regenerate
it with that box ticked.

**Nothing runs at all after setup**
Open the Actions tab and check workflows are enabled for the repository. GitHub also
automatically disables scheduled workflows in repos with no activity for 60 days — any
commit re-enables them.

---

# What it costs

Two AI calls per day, both doing live web research: roughly **$0.15–0.50 per run**, so
**$5–15 a month**. Set a spending limit in the Anthropic console if you'd like a hard cap.

GitHub Actions is free for public repositories and uses about 150 of your 2,000 free
monthly minutes on a private one.

---

# A note on the numbers

Market sizes and revenue estimates in these teardowns are produced by an AI model. The
agent is instructed to show its arithmetic and label every figure with its basis and a
confidence level, and it flags in the "confidence notes" section wherever the public
evidence was thin.

Treat them as a well-reasoned starting hypothesis — good enough to sharpen your own
thinking, not good enough to put in a board deck without checking the source links first.
Every teardown includes the URLs it used.
