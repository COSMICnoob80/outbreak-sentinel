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

---

## 📊 CURRENT STATE (2026-10-15) — REPOSITIONING: universal platform + pitch kit

### Decision (Director + Signal Architect)
Reposition from a single-vertical dengue app to a **universal agentic early-warning
platform**. Bio-surveillance is the *first vertical*, not the product. The moat is the
**receipt ledger**: we issue a signed, falsifiable prediction and later resolve it against
reality (CONFIRMED/REFUTED), so "trust our AI" becomes "check our ledger."

### The adapter/vertical seam (new `verticals/` package, new files only)
- `verticals/base.py` — `Vertical` dataclass (`slug, name, description, subjects,
  subject_label, signal_sources, risk_model, keywords, example_queries, locations,
  forecast_vars, lookback_hours, fusion_role`) + `RiskModel` (`high_means`,
  `escalation_rule`, `downgrade_rule`, `levels`) + `Location`.
- **The seam:** `Vertical.to_config()` compiles a vertical into the exact dict the shipping
  engine already reads (`cities`, `diseases`, `news_keywords`, `social_keywords`,
  `lookback_hours`) plus a `_vertical` metadata block (`signal_sources`, `forecast_vars`,
  `fusion_role`, `risk_model`). So a new domain touches **no engine file**.
- `verticals/__init__.py` — static registry (`VERTICALS`, `get_vertical`, `all_verticals`).
- `verticals/bio_surveillance.py` — the current setup, derived by READING `config.yaml`
  (read-only; config.yaml ownership untouched). 3 verticals total: bio-surveillance,
  `wildfire.py` (news + weather wind/humidity), `supply_chain.py` (news + weather + social).
- `verticals/README.md` — how to add a vertical in ≤50 lines.

### Pitch kit (new `pitch/` package)
`ONE-PAGER.md` (universal pitch, track-agnostic) · `ARCHITECTURE.md` (ASCII diagram, both
seams explicit) · `DEMO-SCRIPT.md` (3-min judge script) · `HACKATHON-FIT.md` (live-verified
fit table). README rewritten to lead with the platform pitch; dengue demoted to a worked
example. Quick-start commands unchanged.

### Verified on disk (2026-10-15)
- `env -u PYTHONPATH .venv/bin/python -m compileall -q verticals` → clean.
- Registry loads 3 verticals; `bio-surveillance` derived **5 cities + 5 diseases** from
  `config.yaml`; `wildfire.to_config()` keys = `cities, diseases, news_keywords,
  social_keywords, lookback_hours`.
- No new runtime dependencies (stdlib `dataclasses`; `pyyaml` already in requirements).
  No edits to owned files (`app.py`, `outbreak_sentinel.py`, `config.yaml`, etc.).

### ⚠️ Hackathon correction (was wrong in prior state)
Prior state recorded "Telegraph Season II, deadline Oct 28." **Conflated two events.**
Verified live 2026-10-15: **AWS CDS Agentic AI Partner closes Oct 28, 2026**;
**Telegraph Hackathon Season II runs Nov 1 – Dec 1, 2026**. Also verified: CodeTheCure
Oct 28 (5:00pm EDT), Qloo Oct 30 (flagged **weak fit** — taste API is a poor domain match),
EthnoHack Nov 2–8, HETIC Nov 4–Dec 18, Agentware Nov 27–30. Sources in
`pitch/HACKATHON-FIT.md`.

### Blocked / not yet wired (plainly)
1. **Fusion prompt is still bio-worded.** `outbreak_sentinel.py`'s `fuse_with_groq` prompt
   hardcodes "outbreak risk analyst" / "most likely disease". The vertical's `fusion_role`
   and `subject_label` are declared in `to_config()` but **not yet consumed** by the engine
   (engine is owned by another agent — not edited here).
2. **Weather vars.** The engine requests only `temperature_2m_max, precipitation_sum,
   weathercode`. Wildfire/supply-chain `forecast_vars` (wind, humidity) are declared but
   **not yet requested** — the seam is documented, not wired.
3. **Channel adapters.** A concurrent agent (Platform Engineer) built a delivery layer
   (`adapters/`: console / webhook / file + `POST /alerts` in `app.py`). That work is
   **not part of this commit and not verified here** (`app.py` is owned by that agent;
   I only read it). SMS/WhatsApp/email (the cloud-track adapter) remain a named seam.

### Concurrent work in this working tree (NOT in this commit)
- `app.py` modified + `adapters/` added by the Platform Engineer (channel seam). Staged
  out deliberately to keep this commit = the repositioning (verticals + pitch + docs) only.
- `history/alerts.jsonl` is gitignored (`.gitignore:18`). `__pycache__/` gitignored (`.gitignore:7`).

---

## 📊 CHECKPOINT 2026-10-15 (late) — platform seams LIVE, fusion gap closed by operator

Supersedes the "Blocked / not yet wired" section above on every point it covers.

### Repositioning shipped: engine + two seams
The project is no longer a dengue app. Core engine is stable and domain-agnostic;
two seams make it universal:
- **`verticals/`** — `Vertical.to_config()` compiles a domain into the exact dict
  `outbreak_sentinel.py:load_config()` already consumes. Adding a domain touches no
  engine file. Registry verified live: `['bio-surveillance', 'wildfire', 'supply-chain']`.
- **`adapters/`** — `Channel.send(card) -> bool`; console / webhook / file. Env-driven via
  `SENTINEL_CHANNELS`. `POST /alerts` is the universal inbound hook — any front-end, chat
  bot or IFTTT-style trigger POSTs a card and it fans out to every channel.

### Real Groq fusion — CONFIRMED (operator closed the blocker)
`config.yaml` model = **`openai/gpt-oss-120b`**. `llama-3.3-70b-versatile` returns 404
`model_not_found` on this key — it is NOT available; the Oct-15 "blocked" note above is
resolved by model choice, not by waiting. Verified in a clean shell
(`env -u PYTHONPATH -u GROQ_API_KEY`), exit 0, zero `rule-based` strings in a full run,
with per-city differentiated output: Karachi HIGH / Lahore MODERATE / Islamabad+Peshawar
LOW, each with distinct drivers and tailored recommendations.

### Verified live (not reported)
- `pytest`: 3 passed. Ledger: 1 line, `status: OPEN`, resolved=0 (honest).
- API via TestClient: `/health`, `/alerts`, `/scoreboard`, `/receipts`, `/cities`,
  `/diseases` → all 200. Existing routes intact.
- `/health` → `{'status':'ok','version':'1.0.0','groq_key_present':True}`; the field
  was proven real (flips false→true→false with/without an injected key).
- `POST /alerts` fan-out → `{'accepted':True,'channels':{'console':True},'delivered':1}`.
- `docker build` succeeded; container HEALTHCHECK `healthy`, ExitCode 0.

### Operator fix — confidence formatting bug
`adapters/console.py` rendered a 0-100 card as "7100%" (used `{:.0%}` on a percent value).
Normalised: values >1 treated as percent, else fraction; `bool` excluded. Both
conventions now render `71%`. Found by live-testing `/alerts`, not by report.

### Still open (plainly, with owners)
1. **Fusion prompt + weather vars not consumed.** `fusion_role`/`subject_label`/
   `forecast_vars` are declared in `to_config()` but `outbreak_sentinel.py` still hardcodes
   bio wording and requests only temp/precip/weathercode. Wildfire therefore *runs* but its
   reasoning is dengue-shaped. This is the next real fix — engine file.
2. **SMS/WhatsApp/email adapter** — named seam, not built. Required for the AWS CDS track.
3. **Container starts with an empty ledger** — `history/receipts.jsonl` is excluded from the
   image and no volume is mounted. Needs a decision before any demo-from-container.
4. **`docker compose` plugin absent** on this host (daemon + buildx present, compose is not).
   Image verified via `docker build` + live container; `docker-compose.yml` is unexecuted here.

### Hackathon eligibility gates (decision-changing — verified live 2026-10-15)
- **AWS CDS (Oct 28, $40K) requires AWS Partner status** — verify BEFORE investing build
  budget in the SMS/WhatsApp adapter for it.
- **CodeTheCure / EthnoHack / HETIC are students-only** — likely ineligible.
- **Telegraph Season II (Nov 1 – Dec 1, open to all, Track 03)** is the unrestricted runway.
- Oct 28 is the **AWS CDS** deadline; Telegraph is Nov 1 – Dec 1. Earlier notes conflated these.
- Full table with per-hackathon angles and live sources: `pitch/HACKATHON-FIT.md`.

---

## 📊 CHECKPOINT 2026-10-17 — Telegraph buying layer LIVE (Track 03 eligibility seam)

### What shipped
- **`telegraph/client.py`** — real REST seam against Telegraph's documented API: miner
  discovery (`GET /miners`), ask (`POST /v1/ask`), and the 402 payment challenge.
  Settlement is **mocked** (no x402 Python SDK / wallet in this env) and every returned
  proof carries `mode="mocked"` + `real_challenge_received`. This is an honest
  **Mechanism build** per Track 03: routing + discovery real, denomination standing in.
- **`telegraph/config.py`** — Chain ID (84532 Base Sepolia), USDC address, RPC, explorer,
  price source, miner selection, settlement mode all **config values, env-overridable**.
  `is_live()` + `TESTNET_BOUNDARY` present. Mainnet flip = config change, not code.
- **`app.py`** (additive) — `POST /telegraph/risk` (paid request → ranked answer +
  settlement proof + risk card), `GET /telegraph/status` (mode/is_live/chain/network/
  boundary/last_settlement), `GET /telegraph/intents` (live miner discovery).
  Existing `/risk`, `/receipts`, `/alerts`, `/health` routes untouched.
- **`dashboard/index.html`** — vanilla JS money-visible front-end: testnet banner
  (unprompted), settlement proof panel with clickable Sepolia tx hash, "Run Risk
  Assessment" button, status bar. No framework, no build step.

### Verified live (TestClient, on disk)
- `/telegraph/status` → 200, full money-visible field set (miner/amount/tx_hash/
  network_label/mode/testnet_boundary). `testnet_boundary` present.
- `/telegraph/intents` → 200, **134 live intents** from the miner discovery endpoint.
- `/telegraph/risk` → 200, top-level miner/amount/tx_hash/network_label + risk_card.
- `/health` → 200. `pytest` → 3 passed. Ledger: 1 line, `status: OPEN`, resolved=0.

### Track 03 rules — compliance status
1. **The agent buys** ✅ — intelligence sourced via Telegraph REST ask, not direct API.
2. **The money is visible** ✅ — miner/amount/tx_hash/network_label first-class JSON +
   clickable Sepolia explorer link on the dashboard.
3. **Machines transact** 🟡 — the ask is autonomous; the settlement leg is mocked
   (Mechanism). A real wallet/x402 integration is required for the Nov 14 checkpoint.

### The one open line to the Nov 14 checkpoint
The checkpoint requires **one settled transaction on the board**. Mocked settlement
does not clear it. Live settlement needs an EVM wallet + x402 client (not installed).
This is the single highest-leverage remaining task before the checkpoint.

### Eligibility gates (unchanged, verified)
Telegraph S2 open to all ✅ · Agentware open to all ✅ (reg opens Oct 26) ·
CodeTheCure/AWS CDS/HETIC/EthnoHack ineligible (students-only / APN-gated).

---

## 📊 CHECKPOINT 2026-10-19 — PWA stale-shell fix shipped + docs housekeeping

### What shipped
- **`dashboard/service-worker.js`** — `CACHE_NAME` bumped `sentinel-shell-v1` → **`sentinel-shell-v2`**.
  The SW serves the shell cache-first, so a v1 cache kept serving the stale `index.html` and the
  committed v2 dashboard never reached returning visitors. The existing `activate` handler already
  deletes every cache whose key ≠ `CACHE_NAME`, so the rename alone forces refresh on next visit.
  No other behavior changed. `dashboard/index.html` untouched — its registration call
  (`register('service-worker.js')`) has no version hint to keep in sync.
- **Docs housekeeping** — PHR records 002–004 added; `deploy/BASE-SEPOLIA-FUNDING.md` runbook
  table prettified.

### Commits (pushed to `origin/main`)
- `55779de` — `docs(phr): PHR records 002-004 + runbook table prettify`
- `a17d67a` — `fix(pwa): bump SW cache so committed v2 dashboard ships past the stale shell`

### Verified
- `node --check dashboard/service-worker.js` clean; `grep -n 'CACHE_NAME ='` → `"sentinel-shell-v2"`.
- `git push origin main` → `3b67cec..a17d67a  main -> main`.

### Note
Returning clients still holding the v1 SW will pick up the v2 worker on their next navigation;
`skipWaiting()` + `clients.claim()` already in the file make the activation immediate.
