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

---

## 📊 CHECKPOINT 2026-10-19 (late) — dashboard v3 integration (Soldier-B)

### What shipped
- **`dashboard/index.html`** rebuilt as **console-v3** (OpenDesign artifact
  `.od/projects/outbreak-sentinel-console/console-v3/index.html`) with the live
  data plumbing ported from the previous dashboard. Single self-contained file:
  no CDN, no external fonts, glyph SVG symbols inline, `prefers-reduced-motion`
  honored, PWA `manifest.json` link + `service-worker.js` registration kept.
- **Live path** — `fetch("/risk")` (async, same-origin, `cache:"no-store"`,
  150 s abort). Response mapped into the v3 card anatomy:
  `city → h3`, `disease → hazard`, `risk_level → sev chip + left rail`,
  `confidence → conf`, `drivers → "Driving signals" line`,
  `recommendation → ACTION line`, `summary → AI chip line`,
  `sources → citation chips showing hostname only, rel="noopener noreferrer"`,
  `chart → 7-point sparkline + min/max/Δ footer`,
  `illustration_hint → glyph strip`. Missing fields hide their section.
  Metric strip/ticker/feed derive only from real `/risk` fields
  (`signals`, `engine`, `risk_cards`, `timestamp`) plus optional `/scoreboard`
  (receipts) and `/telegraph/intents` (masthead count), both degrade silently.
- **Honesty boundary** — live cards are labelled `bio-surveillance` only. The
  wildfire/supply-chain city lists exist **only** in the static demo dataset;
  live filters for those verticals correctly fall through to the empty state.
  `/risk` exposes no numeric score, so the big number is a documented
  level-band + confidence index (`title` attribute says so). `/risk` also
  exposes no hourly series, so the 24H timeline is captioned
  **"calibration preview"** instead of being presented as live fusion.
- **Demo fallback** — the console-v3 8-city dataset renders when the page is
  opened as `file://`, when the fetch throws (backend unreachable/offline),
  when the SW returns its `{offline:true}` 503, or on timeout. A small
  **`demo data`** pill + `engine: demo (static)` + footer stamp make the
  fallback unmistakable.
- **State doctrine** — skeleton on load; empty state on zero cards / filtered
  to zero; error + Retry on HTTP-level failures (server up, `/risk` 5xx).
  No `alert()` anywhere. Untrusted card text is written with `textContent`;
  citation HTML is escaped and non-http(s) URLs (e.g. `javascript:`) rejected.

### Verified
- Extracted the single `<script>` block (31,033 bytes) → `node --check` **PASS**.
- Static cross-check: 28 JS element-ID refs all resolve; no duplicate ids.
- Proof greps: `fetch("/risk")` (line 953), `sparkSVG` + `class="spark-svg"`
  (615/628), `rel="noopener noreferrer"` (678); zero hits for
  `fonts.googleapis|cdn.` and zero `alert(`.
- `git diff --stat -- dashboard/manifest.json dashboard/service-worker.js`
  → **empty** (both untouched, as required).

### Commit
- `05ce03d` — `feat(dashboard): v3 design from OpenDesign run — real /risk wired, static fallback for demo`

### ⚠️ Caveat for the next owner (out of this lane)
`dashboard/service-worker.js` is **cache-first** for `/dashboard/index.html`
and its `CACHE_NAME` is still `sentinel-shell-v2`. Because the SW file itself
did not change, a returning client that already holds the v2 cache will keep
being served the **old** v3 dashboard. Bumping `CACHE_NAME` (e.g. to
`sentinel-shell-v3`) is required to ship this to existing installs — that file
is owned by the Platform Engineer and was intentionally not modified here.

- 2026-10-19 — soldier-C bumped SW cache to sentinel-shell-v3.

---

## 📊 CHECKPOINT 2026-10-21 — LIVE x402 settlement works (Soldier-D)

First **real, on-chain** settlement from `/telegraph/risk`. Two bugs blocked it; both fixed
and verified live against the real engine.

### Bug 1 — escrow accept broke `model_validate` (`telegraph/client.py::_live_settle`)
The engine's 402 challenge carries three accepts:
`exact` @ `eip155:84532` (payable), `exact` @ `solana:EtWTRAB…` (SDK skips unregistered
networks), and `escrow` @ `eip155:84532` **missing the V2 schema's required `asset` and
`maxTimeoutSeconds`**. `PaymentRequired.model_validate(decoded)` rejected the entire
challenge on the escrow entry (2 ValidationErrors), so settlement never ran.
Fix: shallow-copy the challenge, replace **only** `accepts` with entries whose
`scheme == "exact"`, then validate. Rest of the challenge untouched. If no exact accept
survives, `RuntimeError` lists the schemes seen — no silent fallback.

### Bug 2 — settlement KeyError 500'd the endpoint (`app.py::telegraph_risk`)
`settlement["amount_uusdc"]` raised KeyError on the failed-settlement proof shape.
Fix: the `buy_intelligence` call and every settlement field are guarded; all reads use
`.get()`. A failed/incomplete settlement now returns **HTTP 200** with `mode`, `live`,
`engine`, `testnet_boundary`, `settlement_error` (exception text) and `risk_card` as usual.
Settlement logic itself unchanged.

### Live evidence (uvicorn 127.0.0.1:8001, POST /telegraph/risk Karachi/dengue)
HTTP 200. Verbatim fields:
- `mode` = `live`
- `live` = `true`
- `engine` = `llm`
- `network_label` = `Base Sepolia (testnet)`
- `tx_hash` = `0xf2276f58c67f802783f9667e6dfbd74219d3639429d89e30a9b9f8c4c09397d4`
- `amount_uusdc` = `"10000"` (0.01 USDC), `settlement_error` = `null`
- `settlement.mocked` = `false`, `settlement.real_challenge_received` = `true`
- `settlement.rail` = `x402 (live)`

`tx_hash` is a **REAL settle tx from the facilitator's PAYMENT-RESPONSE header**
(`settle.transaction`), not synthesized. Confirmed independently via Base Sepolia RPC
`eth_getTransactionByHash`: `status 0x1`, block `0x2e2a37a`, with a USDC `Transfer` log
from the burner `0x7b3654a6…f249` at `0x036CbD53…dCF7e`.
Explorer (per `TELEGRAPH_EXPLORER_TX_URL`): https://sepolia.basescan.org/tx/0xf2276f58c67f802783f9667e6dfbd74219d3639429d89e30a9b9f8c4c09397d4

### Note for the demo narrative
The purchased answer came back from miner `9002`/`txlens` routed to intent `STORM_ALERT`
with an Air Force base location — the Engine's router chose the intent, and the `/risk`
card is fused separately. The **payment leg** is what this checkpoint proves; answer
relevance for bio-surveillance is a router/query-shaping question, not a settlement one.

### Commits
- `e39e676` — `fix(settlement): exact-scheme accept selection + robust settlement fields in /telegraph/risk` (pushed to `origin/main`)
- this checkpoint — `docs(spine): checkpoint soldier-D live settlement fix`

### Verified
- `env -u PYTHONPATH .venv/bin/python -m compileall -q app.py telegraph` → clean
- `pytest` → **3 passed**
- Server log: no traceback, no ValidationError on the request that settled.

---

## 📊 CHECKPOINT 2026-10-21 — route surgery: console is the default landing (Soldier-F)

### Problem
`GET /telegraph/dashboard` served `static/telegraph.html` — the bare
**"Telegraph Buying Layer (Track 03)"** monospace page — so anyone opening the
dashboard URL (and every demo script) landed on the demo page instead of the
Operations Console. `GET /` returned a JSON payload, so there was no HTML root.

### Route table — BEFORE
| Path | Served |
|---|---|
| `GET /` | JSON `{"status":"ok","service":"outbreak-sentinel",...}` (`health`) |
| `GET /telegraph/dashboard` | `FileResponse(static/telegraph.html)` — **buying layer** |
| `GET /dashboard` | StaticFiles mount (`html=True`) → `dashboard/index.html` (console) |
| `GET /health` | JSON liveness probe |

### Route table — AFTER
| Path | Served |
|---|---|
| `GET /` | **302 → `/telegraph/dashboard`** (`RedirectResponse`) |
| `GET /telegraph/dashboard` | `FileResponse(dashboard/index.html, media_type="text/html")` — **console** |
| `GET /telegraph/buying-layer` | `FileResponse(static/telegraph.html, media_type="text/html")` — demo page, now with a visible `DEMO TOOL` banner |
| `GET /dashboard` | StaticFiles mount, unchanged |
| `GET /health` | unchanged (Railway + Docker healthcheck still point here) |

**Redirect vs mount at `/`:** chose the 302 because `/` previously carried a JSON
health payload whose useful fields already exist at `/health`; a redirect keeps one
canonical HTML URL without changing content negotiation for JSON callers.

### Scope / files touched
- `app.py` — imports `FileResponse, RedirectResponse` at module top; `/` handler
  replaced with redirect; `/telegraph/dashboard` repointed; new `/telegraph/buying-layer`.
- `static/telegraph.html` — one banner `<div>` after `<h1>` (no JS/CSS/settlement changes).
- **Untouched:** `dashboard/index.html`, `dashboard/service-worker.js`, `telegraph/`,
  `.env`, all settlement logic, the `/dashboard` and `/static` mounts.

### Verified
- `.venv/bin/python -m pytest tests -q` → **3 passed** (before) and **3 passed** (after).
- TestClient: `GET /` → `302 /telegraph/dashboard`; `GET /telegraph/dashboard` → `200
  text/html`, title **"Outbreak Sentinel — Operations Console"**; `GET
  /telegraph/buying-layer` → `200 text/html`, `DEMO TOOL: True`; `GET /health` → `200`;
  following `/` yields HTML.
- `git diff --numstat` → only `app.py` (+14/−7) and `static/telegraph.html` (+1/−0).

### Commit
- `d537954` — `fix(routes): / and /telegraph/dashboard serve the Operations Console; buying layer demoted to demo route` (pushed `f83f3de..d537954`)

### Note
`demo/SCRIPT-60s.md`, `demo/SHOTLIST.md` and `pitch/ONE-PAGER.md` still describe
`/telegraph/dashboard` as the money-visible buying layer; that URL now serves the
console. The buying demo URL is `/telegraph/buying-layer`. Docs were not edited here.


---

## 📊 CHECKPOINT 2026-10-21 — console v4: approved Operations Console design (Soldier-E)

### Why
The boss rejected the shipped dashboard: they were seeing the bare monospace
**"Telegraph Buying Layer"** page instead of an operations console. The approved
aesthetic baseline is the prototype at
`~/knowledge-graph/prototypes/outbreak-sentinel.html` ("Outbreak Sentinel —
Operations Console", 33.6 KB). `dashboard/index.html` was rebuilt on that visual
system; its real-data plumbing was kept, not replaced.

### What shipped (`dashboard/index.html`, 78.7 KB, single self-contained file)
- **Prototype visual system, adopted verbatim as tokens:**
  `--bg:#0b0f17 --panel:#111827 --panel-2:#0f1626 --border:#1f2937
  --text:#e5e7eb --dim:#8b98ac --dim-2:#5f6b7f --cyan:#38bdf8 --amber:#fbbf24`,
  same radial background, 12 px panels, 14 px body, 1280 px shell.
- **Translated pieces:** header (glowing dot + tagline + badges + Telegraph-link
  intent pill), Telegraph intents ticker (paused on hover, duplicated track for a
  seamless loop), 25 % / 75 % `.grid` (Live Signal Feed | Risk Cards), severity-rail
  cards (`.card.lv-*` left rail + hover/pin `.detail`), `.sig` feed items with
  news/weather/social family chips, 24 h timeline strip with Play/scrub and peak
  readout, footer disclaimer.
- **Kept plumbing:** `fetch("/risk")` (no-store, 150 s AbortController), engine
  badge (`engine: llm|rule-based`), full card mapping for
  `risk_level/confidence/drivers/recommendation/sources/summary/chart/
  illustration_hint`, sparkline renderer (`sparkSVG`, 150x38), citation chips
  hostname-only with `rel="noopener noreferrer"`, `/scoreboard` receipt metric,
  `/telegraph/intents` count, skeleton -> empty -> error+Retry, `textContent` for
  all untrusted text, zero `alert()`.
- **Metric strip (5):** Signals 24h, Cards, Engine, Settlements, Receipt integrity.
- **Demo fallback retained but labelled:** static 8-city dataset only on
  `file://` / unreachable / timeout, with a `demo data` pill, `engine: demo
  (static)` and a footer stamp. Never mixed into live cards.
- **Embedded settlement section ("Telegraph Settlement — Buying Layer"):** query
  input, city input, disease select, **Buy through Telegraph** -> `POST
  /telegraph/risk` -> styled receipt card rendering `mode`, `live`, miner,
  amount (USDC), network + chain, rail, receipt hash, and `tx_hash` as a styled
  link to `https://sepolia.basescan.org/tx/<hash>` (overridden by
  `explorer_tx_url` from `/telegraph/status`), plus the returned `risk_card`
  (city/disease/level/confidence/summary/drivers/recommendation). Green
  **LIVE SETTLEMENT PROVEN** chip only when `live === true && tx_hash &&
  settlement.mocked === false`; `settlement_error` renders as an amber note.
  Failure -> styled inline error + Retry (re-submits the last payload).
- **`dashboard/service-worker.js`:** `CACHE_NAME` `sentinel-shell-v3` ->
  **`sentinel-shell-v4`** (one line). `manifest.json` untouched.

### Dev note — honesty boundaries kept
`/risk` still exposes no numeric score and no hourly series, so the big number is
the level-band + confidence index (documented in its `title`) and the timeline is
captioned **"calibration preview"**. Live cards are labelled `bio-surveillance`
only; wildfire/supply-chain city lists exist only in the demo dataset, and those
filters correctly fall through to the empty state. Ticker amounts are labelled as
the **observed ask price from the latest 402 challenge** — Telegraph's intents
endpoint returns `miner_count`, not per-intent prices, so no per-intent quote is
invented.

### Verified (on disk, live)
- Extracted the single `<script>` (42,089 bytes) with `python3` -> `node --check`
  **PASS**; `node --check dashboard/service-worker.js` **PASS**.
- Static cross-check: 69 ids, **0 duplicates**; all **43** JS `$("#...")` refs
  resolve; `alert(` count **0**.
- `uvicorn app:app --host 127.0.0.1 --port 8001` (env -u PYTHONPATH):
  `GET /risk` -> **200** in 13.0 s, `engine: llm`, **5 cards** (Karachi/Lahore/
  Islamabad/Peshawar/Quetta, each with drivers + 5 sources + 7-point chart);
  `GET /dashboard/` -> **200** (78,742 bytes); `GET /telegraph/status` -> **200**
  (`mode: live`, `explorer_tx_url` present). Server killed afterwards.
- Grep proofs in the served shell: `fetch("/risk")` x1, `Buy through Telegraph`
  x2, `LIVE SETTLEMENT PROVEN` x1, `sepolia.basescan.org/tx/` x1,
  `--cyan:#38bdf8` and `--amber:#fbbf24` x1 each.
- `git diff --stat` before commit: only `dashboard/index.html` and
  `dashboard/service-worker.js` (+1100/-677).

### Commit
- `20069c7` — `feat(console): v4 — approved Operations Console design + live /risk data + embedded settlement panel`

### Open / for the next owner
`EXPLORER_TX` defaults to the Sepolia basescan URL and is upgraded from
`/telegraph/status` at runtime; `/telegraph/status` remains the only source for
`explorer_tx_url`. Docs describing the dashboard as the buying page (Soldier-F
note above) are unchanged.

---

## 📊 CHECKPOINT 2026-10-22 — console v5 polish (Soldier-G)

### Why
Boss eyeball-verified console v4 in a live browser (fed by `/risk` on port **8001**, owned by
another process — not touched here). Their findings drove four card fixes, global-lead
grouping, and a layered (non-jargon) chain receipt.

### What shipped (`dashboard/index.html` only, single self-contained file)
- **A1 — dead chip removed.** `CLICK TO PIN DETAILS` tag and its `.tag.pin-hint` CSS deleted.
  Detail still reveals on desktop hover and toggles/pins on click (touch); cards now also
  carry `aria-expanded`.
- **A2 — asked vs returned.** Receipt renders a dim `ASKED: <form disease> → engine returned:
  <returned disease>` line **only when they differ** (case/whitespace-insensitive compare).
- **A3 — per-item signal estimates.** Feed items no longer repeat the card-level score. Each
  source item gets `est. <n> ▲/▼ · conf <x.xx>` from its **own headline**: hot keywords
  (outbreak/deaths/surge/cases/positive/admission/…) raise, cool keywords (routine/vaccine/
  decline/calm/stabil/…) lower, plus a deterministic FNV-1a `hash32(headline)` jitter and
  confidence wobble. Same headline → same estimate (verified: 4 real headlines yielded 50, 15,
  12, 17 vs base 44, 14, 15, 15). Labelled `est.` with a tooltip: not a separate engine score.
- **A4 — always-on mini sparkline.** New `.card-foot` row on **every** card. Series source:
  **`risk_cards[].chart[].value`** (7 points as returned by `/risk`) when present; otherwise
  the dashboard's existing 24-point `TL` calibration array, captioned `24h calib.` with a
  tooltip stating it is aggregate (no per-city series was returned). Full chart unchanged in
  the expanded detail.
- **B — global leads grouping.** `renderCards` partitions the already-sorted list with a
  UI-only Pakistani-city index and renders `PAKISTAN` then `GLOBAL` section labels; a header
  is omitted when its group is empty. No truncation: every card `/risk` returns is rendered.
  **No change** to `app.py`, `outbreak_sentinel.py` or `config.yaml` city config.
- **C — chain parameters, layered.**
  - **C1** top strip `SETTLED ON-CHAIN` + chain badge (`BASE SEPOLIA`, derived from
    `network_label`) + short tx (`0xab12…ef34`); click/Enter expands full hash, explorer link,
    and (PRO) the block, looked up lazily via `eth_getTransactionByHash` against
    `state.status.rpc_url` — the API returns no block, so it is never invented.
  - **C2** settled cards get a quiet card-foot chip `✓ receipt 0xab12…ef34` (explorer link,
    `stopPropagation` so it does not toggle the pin). Only for cards matched to a **paid**
    settlement via a `city|disease` map populated from the returned `risk_card`.
  - **C3** one-sentence explainer under the settlement panel header: “Every paid assessment is
    notarized on Base — a tamper-proof receipt nobody can alter.”
  - **C4** one `SIMPLE / PRO` toggle in that header (default **SIMPLE**, persisted in
    `localStorage["sentinel.chainMode"]`, body class `chain-pro`). `.pro-only` rows are hidden
    by **default CSS** (safe even if JS never runs); PRO reveals miner, `amount_uusdc`
    micro-units, chain id / `eip155:` / USDC address, scheme (`rail` + EIP-3009), receipt hash,
    and block hex. SIMPLE keeps: amount in $, network name, mode/live + proven chips, tx strip.
- **D** `dashboard/service-worker.js` `CACHE_NAME` `sentinel-shell-v4` → **`sentinel-shell-v5`**
  (one line). `manifest.json` untouched.

### Honest finding on the 10-city premise
`GET /risk` did **not** return 10 cities in either probe. First probe (200, 8.9 s):
**8 cards — Karachi, Lahore, Islamabad, Peshawar, Quetta, Surat, Rome, Colombo**.
Verification probe (200, 6.3 s): **5 cards — Karachi, Peshawar, Lahore, Islamabad, Quetta**
(LLM fusion is non-deterministic). None of Ludhiana / Amritsar / South Carolina / Alaska /
Netherlands appeared. The dashboard was **not** filtering (it rendered all 8); grouping is now
visible and future global cities will land under `GLOBAL` automatically.

### Verified (own uvicorn on 127.0.0.1:8002 — 8001 untouched)
- Extracted inline `<script>` (51,521 bytes) → `node --check` **PASS**;
  `node --check dashboard/service-worker.js` **PASS**.
- Static: 72 ids, **0 duplicates**; all **46** `$("#…")` refs resolve; `alert(` = 0;
  **0** external `http(s)` `src/href` in the shell (no CDN/fonts).
- `GET /risk` → **200**; `GET /telegraph/dashboard` → **200**, 92,005 bytes.
- Served-HTML greps: `SETTLED ON-CHAIN` 1, `SIMPLE` 3, `PRO` 4, `ASKED:` 1, `PAKISTAN` 1,
  `GLOBAL` 1, `est.` 2, `chainMode` 6, `notarized on Base` 1, `pro-only` 10,
  `CLICK TO PIN` **0**, `pin-hint` **0**.
- Grouping/estimator proven by executing the actual extracted helpers in Node against the
  8-card payload: `PAKISTAN [Karachi, Lahore, Islamabad, Peshawar, Quetta]`,
  `GLOBAL [Surat, Rome, Colombo]`, both headers emitted.
- Server on 8002 killed after the run; the process on 8001 was never touched.

### Commits
- `4fef68a` — `feat(console): v5 — per-item signal scores, always-on sparkline, global leads grouping, layered chain receipts (SIMPLE/PRO)` (pushed `321e6f8..4fef68a`)
- followed by `docs(spine): checkpoint soldier-G v5 polish`

### Open / for the next owner
- The engine's own card scores do not exist (`/risk` exposes no numeric score); the big number
  and the mini-sparkline axis remain documented level-band + confidence derivations.
- `chart` values from the live engine were mostly `0.0` in both probes, so several mini
  sparklines render as honest flat lines; no synthetic series were substituted.
- A live `POST /telegraph/risk` was **not** fired in this pass (no testnet spend), so the
  receipt's C1/C2 rendering is syntax- and field-verified, not settlement-run-verified.
