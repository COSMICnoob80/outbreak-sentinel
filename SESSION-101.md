# SESSION 101 — Outbreak Sentinel (cold-resume brief)

**Written:** 2026-10-14
**Source:** Hermes/Discord session — mirror of the chat summary; edit both together.

## What it is
Bio-surveillance early-warning agent for Pakistan cities (Karachi, Lahore, Islamabad, Peshawar, Quetta).
Fuses news + weather + social signals → per-city risk cards.
Hackathon: **Telegraph Season II** (Oct 28 deadline; same date as AWS Agentic AI track).

## The moat (why this wins)
The **receipt engine**: every HIGH/CRITICAL risk call is published as a sha256-hashed,
append-only receipt; a human later resolves it (CONFIRMED/REFUTED) against an official
source. Verifiable prediction-vs-outcome track record = the demo story.

## Shipped (commits on main)
- `d562424` env fix — feedparser was the only missing dep
- `37bb3f9` `receipts.py` + 3 TDD'd tests — append-only JSONL, content-hash IDs (idempotent)
- `e26b23c` `publish.py` — HIGH/CRITICAL cards persist as receipts
- `f263fc4` API `/receipts` (+`?status=`), `/receipts/{id}` (404 unknown), `/scoreboard`;
  plus `verify.py` CLI resolver
- `eb9459f` SPINE.md corrected + `state/hackathon-state.md` created

## Verified working
- Tests: 3 passed
- API live (uvicorn): scoreboard/404/resolve paths all confirmed
- Agent runs end-to-end, exit 0, no traceback

## Open blockers (fix before demo)
1. **Groq fusion never runs** — `config.yaml` model is literally `rule-based` → 404 → silent
   rule-based fallback every run. Fix: set a real model id (e.g. `llama-3.3-70b-versatile`).
   Key itself is valid.
2. **Synthetic receipt in `history/receipts.jsonl`** (rcpt-9575593f78c6, fake DGHS citation)
   — test artifact. Remove it; demo receipts must come from real runs resolved against real sources.

## Environment notes (this box)
- Use `/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3`
- That venv has **NO pip module** — install with:
  `uv pip install --python /home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 <pkg>`
- Run server: `.../venv/bin/python3 -m uvicorn app:app --port 8010` (background=true)

## Spec deviation on record
The plan's verbatim `resolve()` failed its own test (appended event but never updated
in-memory state). Patched to set both. Tasks 4–6 shipped in one commit (they verify against
the same server).

## Next actions (from plan)
Day 1: fix blockers above (dispatch to Command Code, verify on disk).
Day 2: real runs → real receipts → verify vs real sources.
Day 3: demo pitch + runbook + scoreboard screenshots.
