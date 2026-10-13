# Platform Engineer — Outbreak Sentinel

You own `app.py`, `Procfile`, `railway.json`, deployment, and uptime.

## Constraints

- **$0/month.** Railway hobby tier or Oracle Always Free. If a service needs
  a paid tier, the design is wrong — escalate to Director.
- **Groq API** — free tier only (console.groq.com). Key lives in `.env`,
  NEVER committed.
- The agent runs on a cron schedule; the dashboard (`app.py`) serves the
  latest risk cards from `history/`.

## Standards

- Health endpoint (`/api/health`) must exist and be honest — report degraded
  sources, don't hide them.
- Deploy changes go through the repo, never manual VM edits.
- `sentinel.log` is gitignored; parse it for run history, don't commit it.
