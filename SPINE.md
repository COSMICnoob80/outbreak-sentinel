# SPINE — OUTBREAK SENTINEL

**Purpose:** single source of truth to resume work cold. Read this first in any new session.

- Updated: 2026-10-15
- Repo: `~/telegraph-hackathon/outbreak-sentinel/` (local, git initialized; initial impl committed eccb542)
- Type: Bio-surveillance early-warning agent
- Stack: Python, Groq LLM (free tier), cron-based
- Status: **Core agent built + committed; studio team scaffolded 2026-10-13**

---

## 📊 CURRENT STATE (2026-10-13)

### Implementation (committed eccb542; env fixed + receipt engine added 2026-10-13)
- `outbreak_sentinel.py` (507 lines) — signal fusion agent
- `app.py` — FastAPI dashboard: `/risk`, `/receipts`, `/receipts/{id}`, `/scoreboard`, `/cities`, `/diseases`
- `config.yaml`, `requirements.txt`, `Procfile`, `railway.json` — Railway deploy
- `.gitignore` — `.env` excluded (NEVER commit the Groq key); `history/receipts.jsonl` IS committed
- `receipts.py` + `publish.py` — append-only receipt ledger; HIGH/CRITICAL cards persist as sha256-hashed receipts
- `verify.py` — manual resolver: `python verify.py <id> CONFIRMED|REFUTED "<source>"` records the resolution in the ledger
- `tests/test_receipts.py` — 3 passing tests (deterministic ids, append-only resolve, reload survival)
- `history/receipts.jsonl` — first receipt verified 2026-10-13 (rcpt-9575593f78c6, CONFIRMED)

### Studio Team (2026-10-13)
`AGENTS.md` router + 5 personas in `agents/`:
- **Director** — scope/deadlines/SPINE (mission: Telegraph Season II hackathon, Oct 28 — SAME deadline as AWS Agentic AI; sources synced from `state/hackathon-state.md`)
- **Signal Architect** — fusion logic, calibration, false-positive budget
- **Data Scout** — signal sources + verification
- **Platform Engineer** — FastAPI/Railway/Oracle, $0 budget
- **Domain Guard** — medical red lines, no advice/no panic

### Hackathon Vector (decided 2026-10-13)
- **Primary: Telegraph Season II hackathon — AWS CDS Agentic AI Partner (lablab.ai, Sep 14–Oct 28, $40K)**
- Fallback: CodeTheCure (Devpost, Oct 10–28)
- Why: the moat is agentic orchestration (the studio-team pattern itself is
  the demo), not the health domain

---

## 📊 CURRENT STATE (2026-10-11)

### What It Is
An autonomous bio-surveillance agent that fuses multiple intelligence signals to detect outbreak signals **before official health systems announce them**.

### Architecture
```
NEWS_SEARCH ──────┐
TWITTER_SEARCH ───┤
SENTIMENT_ANALYSIS ┼──→ signal fusion (Groq LLM) ──→ OUTBREAK RISK CARD
WEATHER_FORECAST ──┤
STORM_ALERT ───────┘
```

### Sample Output
```
⚠ Dengue, Karachi — HIGH
drivers: 340% news uptick + monsoon rain + panic score 0.81
```

### Why It Matters
- User is a medical officer (MBBS) — domain moat
- Dengue/malaria/cholera outbreaks leave digital exhaust days before ministries confirm
- Siberian lab outbreak (2026) proves the need is real and current
- Hackathon-ready: fits CodeTheCure (Oct 10-28) or AWS Agentic AI (Oct 28 deadline)

### Telegraph Hackathon Ecosystem
- Primary entry: RxTruth (github.com/COSMICnoob80/rxtruth)
- This is a Track 3 concept, preserved as a parked blueprint
- Uses Telegraph intents: NEWS_SEARCH, TWITTER_SEARCH, SENTIMENT_ANALYSIS, WEATHER_FORECAST

---

## 📋 NEXT STEPS

1. **Verify subagent output** — check `outbreak_sentinel.py`, `config.yaml`, `requirements.txt`
2. **Add Groq API key** — free tier at console.groq.com
3. **Test the agent** — run it manually, verify risk card output
4. **Set up cron** — daily scan for outbreak signals
5. **Consider hackathon entry** — CodeTheCure or AWS Agentic AI

---

## 🔴 RED LINES

- **No medical advice** — this is surveillance, not diagnosis
- **No panic** — risk cards must be calibrated, not alarmist
- **Verify sources** — outbreak claims must be traceable to real data
- **Privacy** — no personal health data collection

---

## 📊 CURRENT STATE (2026-10-15) — appended, supersedes build state above

### Groq fusion: three independent bugs — 2 fixed, 1 blocked
1. **`.env` never loaded (FIXED).** No Python file loaded `.env`; only `outbreak_sentinel.py:281` read `os.environ`. Added a stdlib-only `load_env_file()` (`outbreak_sentinel.py:27-44`) called at module import (`:47`) — parses `KEY=VALUE`, strips quotes, skips blanks/`#comments`, never overwrites an existing env var. No new dependency (python-dotenv deliberately not added). Verified in a clean shell (`env -u GROQ_API_KEY`): key resolves to a 56-char `gsk_` value. `app.py` does **not** need the loader — it has no `os.environ` usage.
2. **`config.yaml` model literal (FIXED).** `config.yaml:59` was `model: "rule-based"` — a literal that 404s and overrode the correct default via the dict-merge. Set to `llama-3.3-70b-versatile`.
3. **Model not available to this key (BLOCKED — operator decision).** Fusion is now attempted (bug 1 fixed), but Groq returns verbatim:
   `404 - {'error': {'message': 'The model \`llama-3.3-70b-versatile\` does not exist or you do not have access to it.', 'type': 'invalid_request_error', 'code': 'model_not_found'}}`
   `client.models.list()` for this key exposes 11 models; `llama-3.3-70b-versatile` is **not** among them. Text models available: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`, `qwen/qwen3.8-27b`, `allam-2-7b`. **Real LLM fusion is NOT yet confirmed** — config left at `llama-3.3-70b-versatile` per instruction (no guess-replace). Operator picks the model.

### Ledger honesty (fabricated event purged)
- Removed one synthetic `{"_event":"resolve", …}` line from `history/receipts.jsonl` — its cited source, "DGHS Pakistan weekly bulletin 2026-11-07", is dated in the **future** relative to the receipt's `2026-10-13` issue date.
- `receipts.py` has no un-resolve/rewrite helper (only `append`/`resolve`), so the line was hand-removed; `receipts.py`/`publish.py` semantics unchanged (append-only going forward).
- Ledger now: **1 line, `status: OPEN`**, no resolution event. Scoreboard: `total_receipts=1, resolved=0`.
- `tests/test_receipts.py`: **3 passed**.

### Housekeeping
- `sentinel.log` truncated to 0 bytes (stale pre-env-fix `ModuleNotFoundError: No module named 'feedparser'` tracebacks). Gitignored (`.gitignore:14`) and untracked — never ships.
- Recreated the uv venv (`.venv`, Python 3.12) from `requirements.txt` — `groq` was absent from the host interpreter. Harness caveat: `PYTHONPATH` points at a Python 3.14 site-packages, so runs must use `env -u PYTHONPATH .venv/bin/python …` (else `pydantic_core` import fails).
