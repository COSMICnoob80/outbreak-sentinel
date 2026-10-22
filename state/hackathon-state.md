# Hackathon State — OUTBREAK SENTINEL

**Single source of truth for deadlines, targets, and track selection.**
Director persona updates this; SPINE.md links here.

- Updated: 2026-10-22
- Primary: **Telegraph Season II — AWS CDS Agentic AI Partner** (lablab.ai, Sep 14–Oct 28, $40K)
- Deadline: **2026-10-28** (both Telegraph Season II and the AWS Agentic AI track share this date)
- Fallback: CodeTheCure (Devpost, Oct 10–28)
- Track rationale: the moat is agentic orchestration — the studio-team pattern itself is the demo, not the health domain.

## Build State (2026-10-15)
- **Real Groq LLM fusion LIVE** on `openai/gpt-oss-120b`. Per-city differentiated reasoning
  confirmed: Karachi HIGH / Lahore MODERATE / Islamabad+Peshawar LOW, each with distinct
  drivers and tailored recommendations. Zero "rule-based" strings in a full run.
- `.env` loaded via a stdlib-only loader in `outbreak_sentinel.py:27` — no python-dotenv
  dependency (the project venv is uv-built; dependency churn has burned this project before)
- Receipt ledger honest: 1 receipt, `status: OPEN`, `/scoreboard` resolved=0. The
  future-dated "DGHS bulletin 2026-11-07" resolve event was purged 2026-10-15. Ledger
  remains append-only; `receipts.py`/`publish.py` semantics untouched.
- 3 tests passing. Sentinel log cleared and gitignored. All commits pushed (working tree clean).
- ⚠️ Groq model availability: `llama-3.3-70b-versatile` (the original design's assumption)
  returns 404 `model_not_found` on this account. Live account exposes 11 models; strongest
  reasoning option is `openai/gpt-oss-120b`. Verify with GET /openai/v1/models.
- ⚠️ Project now has its own `.venv` (Python 3.12) because `groq` was absent from the host
  interpreter. Run as `env -u PYTHONPATH .venv/bin/python` — the harness exports a PYTHONPATH
  into a Python 3.14 site-packages that otherwise breaks the venv.
- Receipt engine live: publish.py persists HIGH/CRITICAL cards; verify.py resolves them; API exposes /receipts, /receipts/{id}, /scoreboard

## v5 Console (2026-10-22)
- **Console v5** — layered `SETTLED ON-CHAIN` receipt strip with one SIMPLE/PRO toggle (jargon hidden
  by default), PAKISTAN/GLOBAL card grouping, per-item `est.` signal scores from each headline, and an
  always-on card-foot sparkline on every card.
- **Live settlements verified on-chain** (Base Sepolia, 0.01 USDC per paid ask):
  - `0x3825fa28…` — block **48410853**
  - `0xfbfe793e…` — block **48407506**
  - `0xf2276f58…` — verified 2026-10-21, block recorded in SPINE checkpoint soldier-D
  - burner `0x7b3654…` holds **19.97 USDC** after the settlements
- **Demo media kit** — `demo/SCRIPT-60s.md` timed judge script, `demo/SHOTLIST.md` 14-shot capture
  plan, `demo/HACKATHON-SUBMISSION.md` one-page brief (local demo URL, judged-tracks map, limits).
- Commits: `4fef68a` (v5 feature set) · `dce42d4` (full-width card-foot sparkline + headless smoke).
