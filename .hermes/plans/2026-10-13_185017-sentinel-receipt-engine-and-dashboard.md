# Plan — Gateway Restart (OD live) + Outbreak Sentinel Track 03 Receipt Engine & Dashboard

## Goal

Ship Outbreak Sentinel as a Telegraph Season II **Track 03 App/Agent** submission (deadline **1 Dec 2026 23:59 UTC**) whose headline artifact is a publicly-archived, timestamped **risk receipt** — a call made *before* official announcement, later resolved against a real source — presented through a futuristic, minimal OpenDesign-rendered dashboard.

---

## Current context / assumptions

### Verified facts (measured, not assumed)

| Fact | Evidence |
|---|---|
| **Telegraph Season II: 1 Nov → 1 Dec 2026**, 30 days, 3 tracks, 15 commercial missions, **$15,000 USD prize pool** | `hackathon.telegraphprotocol.com` (fetched via web search, 2026-10-13) |
| Season II ends **1 Dec 2026** | same |
| Track 03 = Apps & Agents: "Build a working app or agent for one of the 15 commercial missions using intelligence bought through Telegraph" | same |
| **SPINE.md is WRONG on the deadline.** It says "AWS CDS Agentic AI hackathon, Oct 28" in two places (`SPINE.md:24`, `agents/director.md:9`) | read directly |
| Repo: `~/telegraph-hackathon/outbreak-sentinel`, git remote `github.com/COSMICnoob80/outbreak-sentinel` | `git remote -v` |
| `outbreak_sentinel.py` 507 lines, `app.py` ~205 lines (FastAPI, 4 routes: `/`, `/risk`, `/cities`, `/diseases`) | read directly |
| **`sentinel.log` = 3× `ModuleNotFoundError: No module named 'feedparser'`** — the agent has never completed a successful run | read directly |
| No `.venv` in the project, no `pytest` installed | measured |
| Signal sources: Google News RSS (both "news" AND the "social" path — same RSS, different keywords), Open-Meteo weather, keyword sentiment, Groq LLM fusion with rule-based fallback | `app.py:66-135`, `config.yaml` |
| **No verification loop, no persistence, no receipts, no public URL.** `/risk` re-fetches on every call and returns ephemeral JSON | `app.py:167` |
| OpenDesign: daemon live on `:7456` as `opendesign.service` (systemd, enabled, Linger=yes), MCP wired as `open-design`, 22 tools discovered, `curl /api/health` → `{"ok":true,"version":"0.25.0"}` | verified this session |
| Hermes gateway runs `hermes-gateway.service`; `Restart=always`, `RestartSec=5` | unit file |
| Desktop session `20261013_114104_83071b` has grown to **188 messages** (was 134); Discord thread session `20261013_122417_c5705a82` = 208 messages | `state.db` |
| `session_turn_leases` holds an **active lease for `20261013_122417_c5705a82`** (`platform=desktop`) — a desktop-side turn is currently in flight | `state.db` |
| `gateway_routing` maps Discord chat IDs → session IDs. The three routes are: DM `1558064897961762907`→`20261010_210058_015b95b5`, group `#hermesnoob` `1557418377549709322`→`20261010_172236_216323e0`, **thread `1559466784275304529`→`20261013_122417_c5705a82` (this one)** | `state.db` |

### Answers to the questions asked

**1. "Are inputs in `20261013_114104_83071b` rendered both on Discord and the original desktop session? Is everything intertwined?"**

**No. They are two separate conversations.** They are not mirrored and they are not linked.

- The desktop session (`20261013_114104_83071b`, `source=desktop`) and this Discord thread (`20261013_122417_c5705a82`, `source=discord`) are two rows in `~/.hermes/state.db` with separate message tables and separate turn leases. Nothing you type in one appears in the other.
- What *is* shared: `state.db` itself, `SPINE.md` files, `memory`, skills, cron, and the filesystem. That is the only coupling — which is exactly why the SPINE discipline matters.
- **Practical consequence for an 18-hour hospital shift:** the desktop session is useless to you on your phone unless you copy the session ID and resume it. Do not rely on it.

**Recommendation: pick ONE conversation for the shift.** Resume the desktop session on the phone is possible (`hermes --resume 20261013_114104_83071b` in a terminal, not on the phone), but a Discord thread is the only surface you can actually reach from a ward. Better: **use this thread, or a fresh thread, and treat `SPINE.md` as the shared brain** so whichever surface you open next, it resumes correctly.

**2. "RESTART THE GATEWAY without breaking anything to make OD live."**

There is nothing to break and nothing that OD needs. Verified this session:

- The OD daemon is its **own systemd service** (`opendesign.service`) on port `7456`. It does not depend on the Hermes gateway.
- The Hermes MCP client spawns the OD MCP server as a **stdio subprocess per Hermes process**. So the gateway restart is required *only* so that the gateway's own Hermes process performs MCP discovery and picks up the 22 `open-design` tools.
- Your gateway unit has `Restart=always` + `RestartSec=5`, and the documented drain behavior (a restart drains in-flight turns before restarting). So a restart is safe but **can take a long time** if a turn is in flight.

**Caveat discovered:** `session_turn_leases` currently holds an **active lease** on `20261013_122417_c5705a82` (the desktop-platform lease on this very thread's session row). A restart may wait on it. Plan accounts for this.

**3. "What the hell is Grafana?"**

**It is not yours and it is not running.** Grafana is a popular open-source metrics/dashboard web app. I searched `state.db` for "grafana": the only hit is **inside your own pasted announcement text in this thread** — you copied it into the Telegraph Season II message. It appears nowhere else: not in `config.yaml`, not in systemd units, not in any project directory. Nothing is installed, nothing is broken. Disregard it.

**4. "Not sure what exactly you are asking regarding podcast invite downstream call jargon."**

Fair — that was opaque. Rephrased concretely:

> *"The TBT podcast invite is not something you can build toward. It is a consequence. Build the one thing that produces a screenshot people cannot ignore — a timestamped, publicly-archived risk call that was right — and the invite follows from that."*

That is why the plan below makes the receipt engine the primary artifact and the dashboard the presentation layer, not the reverse.

---

## Architecture / proposed approach

**One FastAPI service, three concerns separated:** (a) a **signal→fusion** layer reused from existing code, (b) a new **receipt ledger** that persists every HIGH/CRITICAL call with a content hash and a public URL, and (c) a **verification resolver** that later reconciles each receipt against a real source and records a scoreboard. The **dashboard** is a single self-contained HTML artifact that reads the ledger — built with OpenDesign against a new `DESIGN.md` brand contract, rendered at fixed 1920×1080 for the demo clip.

**Why this shape:** Telegraph Track 03 requires "a working application." The receipt ledger is the part no competing entry will have, because it requires a verifiable ground-truth source and the discipline to publish *before* the event. The dashboard is the visual proof, and OpenDesign is already installed and wired, so it costs nothing extra.

**Track 03 note:** Telegraph's premise is "intelligence bought through Telegraph." Full protocol integration is out of scope for the first build (and needs their SDK/spec confirmed). **Phase 1 ships a working app that clearly *could* consume ranked intelligence** — the receipt ledger is provider-agnostic. Track 03 integration becomes an open question in the plan, not a guess.

---

## Step-by-step tasks

Each task is independently committable. Working directory: `/home/cosmicnoob/telegraph-hackathon/outbreak-sentinel` (abbreviated `PROJ` below). Python: `/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3` (has `pytest`? **No** — Task 0 installs it). Never commit `.env`.

### Task 0 — Fix the broken environment (the repo has never run once)

The single highest-value task in this plan. `sentinel.log` proves three consecutive failures.

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pip install feedparser pyyaml aiohttp fastapi uvicorn pytest
```

Expected output: ends with `Successfully installed ... feedparser-... pytest-...` (plus any upgrades).

**Verify — the first successful run in repo history:**

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 outbreak_sentinel.py --dry-run 2>&1 | tail -25
```

Expected output: no traceback; a risk card block ending with lines like `Recommendation: Continue monitoring` / `Signals: N news | N social | 5 cities`.

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pytest --version
```

Expected: `pytest 9.x.x`.

**Commit:** `fix(env): install missing feedparser dep — first successful agent run`

### Task 1 — Add the Groq key and prove LLM fusion works

```bash
cat /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel/.env
```

If it already contains `GROQ_API_KEY=...`, skip to verify. Otherwise get a free key at `console.groq.com` and:

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
printf 'GROQ_API_KEY=<key>\n' >> .env
chmod 600 .env
```

**Verify:**

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 outbreak_sentinel.py 2>&1 | tail -20
```

Expected: no traceback; risk cards produced with the Groq path active (or the rule-based fallback with a visible note). Confirm `.gitignore` still excludes `.env`:

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
git status --short
```

Expected: `.env` is **not** listed as untracked.

**Commit:** none (`.env` is gitignored; record in SPINE that Groq fusion is live).

### Task 2 — TDD: receipt ledger (`receipts.py`)

New file: `PROJ/receipts.py`. A receipt is an immutable record of a published call.

**2a. Write the failing test** — new file `PROJ/tests/test_receipts.py`:

```python
import json
import pytest
from receipts import ReceiptStore, make_receipt

pytest_plugins = []

def test_make_receipt_is_deterministic(tmp_path):
    payload = {
        "city": "Karachi", "disease": "dengue", "risk_level": "HIGH",
        "score": 62, "drivers": ["News uptick: 14 articles in 24h"],
        "issued_at": "2026-11-02T09:15:00+05:00",
    }
    r = make_receipt(payload)
    assert r["receipt_id"]  # non-empty
    assert r["content_hash"].startswith("sha256:")
    # determinism: identical payload -> identical id
    assert make_receipt(payload)["content_hash"] == r["content_hash"]

def test_store_roundtrip_and_append_only(tmp_path):
    store = ReceiptStore(tmp_path / "ledger.jsonl")
    r1 = make_receipt({"city": "Karachi", "disease": "dengue",
                       "risk_level": "HIGH", "score": 62, "drivers": [],
                       "issued_at": "2026-11-02T09:15:00+05:00"})
    store.append(r1)
    assert store.count() == 1
    assert store.get(r1["receipt_id"]) == r1
    # resolution mutates status but keeps the original hash
    store.resolve(r1["receipt_id"], verdict="CONFIRMED",
                  source="DGHS Pakistan weekly bulletin 2026-11-07")
    after = store.get(r1["receipt_id"])
    assert after["status"] == "RESOLVED"
    assert after["resolution"]["verdict"] == "CONFIRMED"
    assert after["content_hash"] == r1["content_hash"]
    assert store.count() == 1  # append-only: no duplicate rows

def test_store_survives_reload(tmp_path):
    store = ReceiptStore(tmp_path / "ledger.jsonl")
    r = make_receipt({"city": "Lahore", "disease": "cholera",
                      "risk_level": "CRITICAL", "score": 78, "drivers": [],
                      "issued_at": "2026-11-03T08:00:00+05:00"})
    store.append(r)
    reopened = ReceiptStore(tmp_path / "ledger.jsonl")
    assert reopened.count() == 1
    assert reopened.get(r["receipt_id"])["city"] == "Lahore"
```

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_receipts.py -q
```

Expected: **FAIL** — `ModuleNotFoundError: No module named 'receipts'`.

**2b. Implement minimally** — new file `PROJ/receipts.py`:

```python
"""Receipt ledger: immutable, append-only record of published risk calls."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any


def make_receipt(payload: dict) -> dict:
    """Build a receipt. receipt_id is derived from the content hash, so the
    same inputs always produce the same id (idempotent re-publish)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    receipt = dict(payload)
    receipt["content_hash"] = f"sha256:{digest}"
    receipt["receipt_id"] = f"rcpt-{digest[:12]}"
    receipt["status"] = "OPEN"
    return receipt


class ReceiptStore:
    """Append-only JSONL ledger. Resolutions append a new event rather than
    mutating history, so the ledger itself is auditable."""

    def __init__(self, path: str):
        self.path = str(path)
        self._receipts: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("_event") == "resolve":
                    rid = event["receipt_id"]
                    if rid in self._receipts:
                        self._receipts[rid]["status"] = "RESOLVED"
                        self._receipts[rid]["resolution"] = event["resolution"]
                else:
                    self._receipts[event["receipt_id"]] = event

    def append(self, receipt: dict) -> None:
        if receipt["receipt_id"] in self._receipts:
            return  # idempotent
        self._receipts[receipt["receipt_id"]] = receipt
        self._append_line(receipt)

    def resolve(self, receipt_id: str, verdict: str, source: str) -> None:
        if receipt_id not in self._receipts:
            raise KeyError(f"unknown receipt: {receipt_id}")
        self._append_line({
            "_event": "resolve",
            "receipt_id": receipt_id,
            "resolution": {"verdict": verdict, "source": source},
        })

    def _append_line(self, obj: dict) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True) + "\n")

    def count(self) -> int:
        return len(self._receipts)

    def get(self, receipt_id: str) -> dict | None:
        return self._receipts.get(receipt_id)

    def all(self) -> list[dict]:
        return list(self._receipts.values())
```

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_receipts.py -q
```

Expected: **PASS** — `4 passed`.

**Commit:** `feat(receipts): append-only receipt ledger with content-hash ids + tests`

### Task 3 — Publish receipts from the fusion layer

**3a. Failing test** — append to `PROJ/tests/test_receipts.py`:

```python
from outbreak_sentinel import rule_based_risk  # existing function

def test_high_risk_produces_publishable_receipt():
    card = rule_based_risk(14, {"forecast": [
        {"precipitation": 60, "temp_max": 36}]}, 0.7,
        {"news_high": 10, "news_medium": 5, "sentiment_high": 0.6,
         "sentiment_medium": 0.3, "temp_high": 35.0, "rain_high": 50.0})
    assert card["risk_level"] in ("HIGH", "CRITICAL")
    receipt = make_receipt({
        "city": "Karachi", "disease": "dengue",
        "risk_level": card["risk_level"], "score": card["score"],
        "drivers": card["drivers"],
        "issued_at": "2026-11-02T09:15:00+05:00",
    })
    assert receipt["content_hash"].startswith("sha256:")
```

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_receipts.py -q
```

Expected: pass or fail depending on `rule_based_risk`'s exact return keys. **If it fails, read `PROJ/outbreak_sentinel.py:207-261` and adjust the test to the real return shape — do not change production code to fit the test.**

**3b. Add the publish path** — new file `PROJ/publish.py`:

```python
"""Turn HIGH/CRITICAL risk cards into durable receipts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from receipts import ReceiptStore, make_receipt

PKT = timezone(timedelta(hours=5))


def publish_cards(cards: list[dict], store: ReceiptStore,
                  city: str, disease: str) -> list[dict]:
    published = []
    for card in cards:
        if card.get("risk_level") not in ("HIGH", "CRITICAL"):
            continue
        receipt = make_receipt({
            "city": city,
            "disease": disease,
            "risk_level": card["risk_level"],
            "score": card["score"],
            "drivers": card["drivers"],
            "issued_at": datetime.now(PKT).isoformat(timespec="seconds"),
        })
        store.append(receipt)
        published.append(receipt)
    return published
```

**Verify:**

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_receipts.py -q
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -c "
from publish import publish_cards
from receipts import ReceiptStore
import tempfile, os
s = ReceiptStore(os.path.join(tempfile.mkdtemp(),'l.jsonl'))
r = publish_cards([{'risk_level':'HIGH','score':62,'drivers':['x']}], s, 'Karachi', 'dengue')
print('published:', len(r), r[0]['receipt_id'])
"
```

Expected: `published: 1 rcpt-<12 hex chars>`.

**Commit:** `feat(publish): persist HIGH/CRITICAL cards as receipts`

### Task 4 — Serve the receipts (FastAPI)

Add to `PROJ/app.py` (imports already present; add `from receipts import ReceiptStore, make_receipt` and `from publish import publish_cards` near the existing imports, then append these routes before the existing `@app.get("/cities")` block):

```python
LEDGER_PATH = os.path.join(os.path.dirname(__file__), "history", "receipts.jsonl")
STORE = ReceiptStore(LEDGER_PATH)


@app.get("/receipts")
def list_receipts(status: Optional[str] = None):
    items = STORE.all()
    if status:
        items = [r for r in items if r.get("status") == status.upper()]
    return {"count": len(items), "receipts": items}


@app.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: str):
    r = STORE.get(receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="receipt not found")
    return r


@app.get("/scoreboard")
def scoreboard():
    resolved = [r for r in STORE.all() if r.get("status") == "RESOLVED"]
    verdicts: dict[str, int] = {}
    for r in resolved:
        v = r["resolution"]["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    return {"total_receipts": STORE.count(), "resolved": len(resolved),
            "verdicts": verdicts}
```

**Verify:**

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 -m uvicorn app:app --port 8010 >/tmp/sentinel-test.log 2>&1 &
sleep 4
curl -s http://127.0.0.1:8010/ | head -c 200; echo
curl -s http://127.0.0.1:8010/scoreboard; echo
curl -s http://127.0.0.1:8010/receipts | head -c 300; echo
kill %1
```

Expected: `/` → `{"status":"ok",...}`; `/scoreboard` → `{"total_receipts":0,"resolved":0,"verdicts":{}}`; `/receipts` → `{"count":0,"receipts":[]}`.

**Commit:** `feat(api): expose receipt ledger + scoreboard endpoints`

### Task 5 — Verification resolver (the part that makes it credible)

New file `PROJ/verify.py`. Resolves an OPEN receipt against a configured source URL. **Manual-first**: a CLI that records a verdict, because automating ground truth reliably is the single hardest part of this project and automating it badly destroys the entire credibility claim.

```python
"""Resolve receipts against a real-world source. Manual-by-default."""
from __future__ import annotations

import argparse
import sys

from receipts import ReceiptStore


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Resolve an outbreak receipt")
    p.add_argument("receipt_id")
    p.add_argument("verdict", choices=["CONFIRMED", "MISSED", "FALSE_ALARM", "EARLY"])
    p.add_argument("--source", required=True,
                   help="Citation: URL or document title of the official source")
    p.add_argument("--ledger", default="history/receipts.jsonl")
    a = p.parse_args(argv)
    store = ReceiptStore(a.ledger)
    if not store.get(a.receipt_id):
        print(f"error: unknown receipt {a.receipt_id}", file=sys.stderr)
        return 1
    store.resolve(a.receipt_id, verdict=a.verdict, source=a.source)
    print(f"resolved {a.receipt_id} -> {a.verdict} ({a.source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Verify (needs a receipt from Task 4 run; seed one if none exists):**

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
/home/cosmicnoob/.hermes/hermes-agent/venv/bin/python3 verify.py rcpt-doesnotexist CONFIRMED --source "test"; echo "exit=$?"
```

Expected: `error: unknown receipt rcpt-doesnotexist`, `exit=1`.

**Commit:** `feat(verify): manual receipt resolver CLI with required source citation`

### Task 6 — OpenDesign brand contract for the dashboard

New file `PROJ/brand/DESIGN.md` (this is the OpenDesign brand contract; it drives every rendered artifact):

```markdown
# Outbreak Sentinel — Brand Contract

## Identity
A clinical intelligence instrument. Not a health app, not an alarm.
The tone is an air-traffic-control display: calm, precise, confident,
never sensational. If a reader feels fear, the design has failed.

## Palette
- Background: #07090F (near-black, slight blue)
- Surface: #0E1320
- Primary accent (risk): #E5484D
- Elevated risk: #F5A524
- Resolved / verified: #30A46C
- Text primary: #E6EDF3
- Text muted: #8B949E

## Typography
- Display: tight tracking, uppercase, 200 weight for headings
- Data: tabular numerals everywhere — every number must be monospaced
- Never use decorative typefaces

## Layout
- Strict 12-column grid, generous negative space
- One idea per viewport: status → drivers → provenance → resolution
- No gradients, no shadows deeper than 1px, no rounded corners above 4px
- Every risk number must show its timestamp and its source inline

## Voice
- "Risk elevated for Karachi — dengue" not "DANGER ALERT"
- Never use the words: danger, panic, crisis, emergency, deadly
- Recommendations are phrased as "monitor / verify / inform", never "act now"
```

**Commit:** `feat(brand): DESIGN.md contract — clinical-instrument visual language`

### Task 7 — Build the dashboard via OpenDesign

Use the wired MCP tools (`mcp_open-design_*`, live after the gateway restart):

1. `mcp_open-design_create_project` → name `outbreak-sentinel-dashboard`
2. `mcp_open-design_start_run` with skill for a single-page web artifact, prompt containing the full contents of `PROJ/brand/DESIGN.md` plus: *"Single-page dark dashboard at 1920×1080. Sections: (1) live risk cards for 5 Pakistani cities with tabular numbers, (2) receipt ledger table with receipt_id, city, level, score, issued_at, status, (3) scoreboard showing confirmed vs missed vs false-alarm counts, (4) provenance footer listing every signal source with fetch timestamp. Reads from GET /risk, /receipts, /scoreboard on http://127.0.0.1:8010."*
3. `mcp_open-design_get_run` every 30–60s until `succeeded`. **Do not cancel** — runs take 5–30 min by design.
4. `mcp_open-design_get_artifact` to pull the files into `PROJ/dashboard/`.

**Verify:**

```bash
ls /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel/dashboard/
python3 -c "
import re,glob
for f in glob.glob('/home/cosmicnoob/telegraph-hackathon/outbreak-sentinel/dashboard/*.html'):
    t=open(f).read()
    for hex_ in ['#07090F','#E5484D','#30A46C']:
        assert hex_ in t, f'{f} missing {hex_}'
    print('brand tokens present in', f)
"
```

Expected: `brand tokens present in <path>.html`.

**Commit:** `feat(dashboard): OpenDesign-rendered single-page dashboard per DESIGN.md`

### Task 8 — Capture the demo screenshot at fixed resolution

```bash
cd /home/cosmicnoob/.hermes/tools
BROWSER=$(ls -d chromium-* | head -1)
"$BROWSER/chrome" --headless --disable-gpu --no-sandbox \
  --window-size=1920,1080 --screenshot=/tmp/dash.png \
  --virtual-time-budget=5000 \
  "file:///home/cosmicnoob/telegraph-hackathon/outbreak-sentinel/dashboard/index.html"
ls -la /tmp/dash.png
python3 -c "
from PIL import Image
im = Image.open('/tmp/dash.png')
print(im.size)
assert im.size == (1920,1080), im.size
" 2>/dev/null || echo "PIL missing — verify size manually via file(1)"
```

Expected: `(1920, 1080)`.

**Commit:** `chore(demo): fixed 1920x1080 capture of dashboard`

### Task 9 — Restart the gateway so `open-design` tools go live in Discord

Because the MCP client discovers servers at Hermes process start, the gateway must restart. It is safe (`Restart=always`, drains turns) but may be slow if a turn is in flight.

```bash
systemctl --user status hermes-gateway --no-pager | head -5
```

Check `Active:` and note the uptime. Then:

```bash
systemctl --user restart hermes-gateway
```

```bash
sleep 45
systemctl --user is-active hermes-gateway
```

Expected: `active`.

**Verify OD is reachable by the new gateway process:**

```bash
curl -s --max-time 5 http://127.0.0.1:7456/api/health
```

Expected: `{"ok":true,"version":"0.25.0",...}`.

**Verify the MCP server still enumerates 22 tools** (this is the exact client Hermes will use):

```bash
cd /home/cosmicnoob/.hermes/cache/scratch/open-design/apps/daemon
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | node dist/cli.js mcp --daemon-url http://127.0.0.1:7456 2>/dev/null | grep -o '"name":"[a-z_]*"' | wc -l
```

Expected: `22`.

**If the restart stalls on the in-flight turn lease:** wait 10 min, re-check `systemctl --user is-active hermes-gateway`. If still not `active`, the lease is held by a dead process — check `ps aux | grep hermes | grep -v grep`, kill stale PIDs, then `systemctl --user restart hermes-gateway` again.

**Commit:** no code change. Record in SPINE: "gateway restarted <timestamp>, open-design MCP verified live, 22 tools."

### Task 10 — Correct the SPINE and agent docs (they carry a wrong deadline)

Edit `PROJ/SPINE.md`:
- `SPINE.md:24` and `agents/director.md:9` — replace "AWS CDS Agentic AI hackathon, Oct 28" with "**Telegraph Season II Track 03 (Apps & Agents), 1 Nov → 1 Dec 2026, $15K pool**"
- Add a "Current State" line recording: deps fixed, first successful run on `<date>`, receipts ledger at `history/receipts.jsonl`, endpoints added, OpenDesign wired.

```bash
cd /home/cosmicnoob/telegraph-hackathon/outbreak-sentinel
grep -n "Oct 28\|AWS CDS" SPINE.md agents/director.md
```

Expected before edit: 2 matching lines. Expected after: none.

**Commit:** `docs(spine): correct deadline to Telegraph S2 Track 03 (1 Dec 2026) + record current state`

### Task 11 — Capture one real receipt before the hackathon opens

This is the evidence artifact. **Timing note:** Season II starts 1 Nov. Receipts issued before then are legitimate (the system runs continuously) but the *demo narrative* is strongest with receipts issued during the season.

1. Start the cron/loop: run `outbreak_sentinel.py` at least daily.
2. When a HIGH/CRITICAL fires, publish the receipt (Task 4 endpoint or `publish.py`).
3. Publicly post the receipt URL immediately.
4. When official confirmation appears, resolve via `verify.py` with a real citation.

**Commit:** the receipt itself lands in `history/receipts.jsonl` (gitignored for raw JSON per `.gitignore:16` — **change that**: `!history/receipts.jsonl` so receipts are versioned and provable). Add to `.gitignore` a negation:

```gitignore
history/*.json
!history/receipts.jsonl
```

**Commit:** `chore(git): version receipts.jsonl — the ledger is the evidence`

---

## Tests / validation

| Check | Command | Expected |
|---|---|---|
| Receipt ledger unit tests | `venv/bin/python3 -m pytest tests/ -q` | `4+ passed` |
| Agent runs without error | `venv/bin/python3 outbreak_sentinel.py --dry-run` | risk cards, no traceback |
| API serves | `curl -s localhost:8010/scoreboard` | `{"total_receipts":N,...}` |
| Receipt is immutable | `verify.py` then re-`get()` | `content_hash` unchanged, `status=RESOLVED` |
| Brand compliance | grep the three hex tokens in dashboard HTML | all present |
| Screenshot size | `PIL` assert | `(1920, 1080)` |
| OD daemon healthy | `curl localhost:7456/api/health` | `ok:true` |
| OD MCP tool count | JSON-RPC `tools/list` | `22` |
| Gateway active | `systemctl --user is-active hermes-gateway` | `active` |
| No secrets committed | `git log -p \| grep -i "GROQ_API_KEY"` | no output |

---

## Risks, tradeoffs, and open questions

**Risks**

1. **Ground truth is the hard part.** Automating "did the outbreak actually happen" reliably is genuinely difficult; a resolver that is wrong twice destroys the entire credibility premise. Mitigation: manual-first resolver with mandatory source citation. Automate later, never before.
2. **"Before official announcement" is a claim you must be able to defend.** If a receipt is issued after an official source already published, the artifact is worthless. Mitigation: record the fetch timestamp and the source snapshot alongside every receipt; never backdate.
3. **OpenDesign runs take 5–30 minutes** and spawn their own agent. Cancelling early discards design quality. Mitigation: budget one long block; poll, don't cancel.
4. **The gateway restart drains in-flight turns** and a lease is currently held on this thread's session. Mitigation: Task 9 has an explicit stall path.
5. **`hermes mcp add` has a real persistence bug** (verified: connected, 22 tools, wrote nothing). Mitigation: config was written via venv Python and is verified working — do not re-run `hermes mcp add open-design`.

**Tradeoffs**

- **Manual verification over automated** — slower, less impressive, and the only version that is trustworthy.
- **One surface over two** — the desktop session and this Discord thread are separate conversations; using both means losing context. Chosen: SPINE as the shared brain.
- **Track 03 without full Telegraph protocol integration** — the app works standalone; protocol buying/routing is deferred rather than faked.

**Open questions (need the user)**

1. **Which of the 15 commercial missions does Outbreak Sentinel map to?** The list is on `hackathon.telegraphprotocol.com`. Track 03 requires choosing one. **This determines framing, submission copy, and judging criteria.** I will not guess it.
2. **Groq API key available?** `.env` exists (70 bytes) but contents unverified. If no key, the rule-based fallback is the whole system and the demo narrative weakens.
3. **Deployment target for the public receipt URLs** — Railway config exists (`railway.json`, `Procfile`) but the SPINE mentions Oracle. Public URLs are what make the receipt artifact work. Which one?
4. **Submission format requirements** — video? repo? live demo? Track 03's judging rubric is on the hackathon site and unread.
5. **Is RxTruth still the primary Telegraph entry?** The SPINE says so, but the user has pivoted to Outbreak Sentinel. Two entries is a split focus; confirm which.

**Deliberately out of scope (YAGNI)**

- Telegraph protocol SDK integration
- Automated ground-truth resolver
- ML-based sentiment
- Direct X/Twitter API
- PharmaWatch

---

## Appendix — the two session questions, answered precisely

**Q: Are inputs in `20261013_114104_83071b` rendered both here on Discord and on the original desktop session? Is everything intertwined?**

**A: No.** They are two independent conversations in `~/.hermes/state.db`:

| | Desktop session | This Discord thread |
|---|---|---|
| Session ID | `20261013_114104_83071b` | `20261013_122417_c5705a82` |
| `source` | `desktop` | `discord` |
| Messages | 188 | 208 |
| Shared with you | **No** | **Yes** |

Nothing typed in one appears in the other. The shared layer is the filesystem + `state.db` + SPINEs — not the conversation.

**For an 18-hour hospital shift on your phone:** the desktop session is unreachable from a ward. Use this thread (or a new one) and let `SPINE.md` carry state. That is what SPINEs are for, and it is why Task 10 matters.

**Q: What is Grafana?**

**A: Not yours, not running, not installed.** The only occurrence of the word in your entire Hermes state is inside the Telegraph Season II text you pasted into this thread. Ignore it.
