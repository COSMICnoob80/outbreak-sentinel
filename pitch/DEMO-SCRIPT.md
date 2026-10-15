# Demo Script — 3 minutes, one take

**Goal:** a judge should leave believing this is a *platform with a verifiable
ledger*, not a dengue dashboard. The last 20 seconds must land on "add your
vertical in 50 lines."

Terminal is full-screen. No slides until the close.

---

## 0:00 – 0:20 — Cold open (the problem)

> "Every early-warning system has the same flaw: it never keeps score. Anyone can
> print a red alert. Nobody comes back a week later to say whether they were
> right. So responders learn to ignore the alerts — and then miss the one that
> mattered."

*(Beat.)*

> "We built the missing half: alerts that issue a signed receipt and later prove
> whether they were right."

---

## 0:20 – 0:50 — Show the loop (don't explain it, run it)

```bash
env -u PYTHONPATH .venv/bin/python outbreak_sentinel.py
```

Let the risk card paint. Read **one** card aloud, drivers and all:

```
🟠 KARACHI — DENGUE — HIGH
   Confidence: 78%
   Drivers:
     • News uptick: 13 articles in 24h
     • Heavy rain forecast: 61.2mm
   Recommendation: Investigate signals
```

> "One lookup per city. Two *independent* signal families had to agree before
> this became HIGH: a news uptick **and** vector-friendly weather. A single
> signal can never escalate a card — that's our false-positive budget, written
> into the calibration rule."

---

## 0:50 – 1:40 — The moat: the receipt ledger

> "Now the part nobody else ships. That HIGH call isn't a printout. It's a
> receipt."

```bash
curl -s localhost:8010/receipts | python -m json.tool
```

Point at `receipt_id`, `content_hash`, `status: OPEN`.

> "The id is the sha256 of the card's content. Change one character and the id
> changes. The ledger is append-only — there is no edit or un-resolve in the
> codebase. It's tamper-evident by construction."

Now resolve it against reality:

```bash
python verify.py rcpt-9575593f78c6 CONFIRMED "DGHS Sitrep, real source"
curl -s localhost:8010/scoreboard | python -m json.tool
```

> "Resolution appends a *new* event — it never rewrites history. And the
> scoreboard is the honest resume: calls made, calls resolved, verdicts.
> **`resolved: 0` is a feature, not a bug** — we only count what a human has
> checked against a real source."

---

## 1:40 – 2:10 — "This isn't a dengue app"

Switch to the verticals (or `ls verticals/`):

```bash
env -u PYTHONPATH .venv/bin/python -c "
from verticals import all_verticals
for v in all_verticals(): print(v.describe(), '\n')"
```

> "Bio-surveillance is just the first vertical. Same engine, same ledger — we
> also ship **wildfire** (news + wind/humidity forecast) and **supply-chain
> disruption** (news + weather + social at trade hubs). The engine never
> changed. Only this file did."

---

## 2:10 – 2:40 — The close (the 50-line promise)

> "Here's why this is a platform and not a vertical slice. A new domain is a
> **~50-line config**: declare the locations, the signals, and — the part that
> matters — write down *what HIGH means*. The fusion, the calibration rule, the
> tamper-evident ledger, and the resolution loop all come for free."

Open `verticals/README.md`, show the template, count the lines.

> "Cloud track — swap the delivery adapter to SMS or WhatsApp. Health track —
> the bio vertical is live today. Agentic track — the studio team and the
> verified ledger. Data track — calibration and an auditable trail. One repo,
> one demo, every track."

---

## 2:40 – 3:00 — Stop talking

Leave `/scoreboard` on screen. Let the judge read the ledger.

---

## Pre-flight checklist

```bash
# 1. server up (background)
env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --port 8010 &
# 2. endpoints answer
curl -s localhost:8010/scoreboard
curl -s localhost:8010/receipts
# 3. the agent runs clean (exit 0, no traceback)
env -u PYTHONPATH .venv/bin/python outbreak_sentinel.py | tail -20
# 4. tests green
env -u PYTHONPATH .venv/bin/python -m pytest tests/ -q
```

Kill the server when done: `kill %1` (or `pkill -f "uvicorn app:app"`).

## Failure drills (say the truth, don't stall)

- **Groq down / no key** → the agent prints "using rule-based risk scoring" and
  emits the same card shape. "We degrade to a transparent scoring rule — it never
  silently fabricates a level."
- **No fresh news** → say so: "LOW means *no signal*, not *no risk*." Show the
  card's confidence, not just its color.
- **Judge asks "how many were you right about?"** → show `/scoreboard`
  unflinchingly. The whole pitch is that the number is checkable.
