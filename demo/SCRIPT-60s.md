# 60-Second Demo Script — Outbreak Sentinel (Telegraph S2 Track 03)

Word-for-word. Timed to the second. ~142 words at ~145 wpm = 59s.
Subtitle-ready: one sentence per line below; drop straight into an SRT.

---

## 0:00 – 0:08 (8s) — The problem

Every early-warning system has the same flaw: it never keeps score.
Anyone can print a red alert.
Nobody comes back a week later to say whether they were right.

## 0:08 – 0:22 (14s) — What it does

Outbreak Sentinel fixes that.
It fuses news, weather, and social chatter with an LLM into a calibrated risk card —
and only when two independent signal families agree.
Then it issues a signed receipt: the sha256 of the card, appended to an immutable ledger.

## 0:22 – 0:37 (15s) — Why Telegraph gave it an edge

New this build: it does not call APIs directly.
It buys ranked intelligence through Telegraph —
parallel paid requests, each routed to the highest-ranked miner, each returning a receipt.
Settlement on Base Sepolia.
The money is on screen: miner, amount, tx hash, network.

## 0:37 – 0:50 (13s) — The moat

A week later we resolve the receipt against a real source — confirmed or refuted.
The scoreboard is the honest track record.
"Trust our AI" becomes "check our ledger."

## 0:50 – 0:60 (10s) — Close

Seven verticals, one engine.
Add yours in fifty lines.
Check our ledger.

---

## On-screen cues (must be visible during each beat)

- 0:00–0:08: dashboard `/telegraph/dashboard`, red testnet banner, status panel (Mode / Network / Chain ID).
- 0:08–0:22: click "Buy through Telegraph"; settlement proof panel + risk card appear.
- 0:22–0:37: zoom settlement proof: miner, amount USD, Sepolia tx hash, clickable link, network label.
- 0:37–0:50: `/scoreboard` and `/receipts` (receipt_id, content_hash, status OPEN).
- 0:50–0:60: `verticals/` listing (7 verticals) or `verticals/README.md` template.

## Pre-flight

Server up: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --port 8000`
Dashboard: http://localhost:8000/telegraph/dashboard
Scoreboard: http://localhost:8000/scoreboard
Receipts: http://localhost:8000/receipts