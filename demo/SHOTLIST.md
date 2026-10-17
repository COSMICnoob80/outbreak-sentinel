# Shotlist — 60-second demo (founder on a laptop)

Assume: laptop, 1080p screen, server already running on :8000.
Pre-flight (run before recording): `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --port 8000`
and open http://localhost:8000/telegraph/dashboard in Chrome, full-screen (F11).

---

## Shot 1 — 0:00–0:08 (8s) — Problem

- Screen: dashboard `/telegraph/dashboard`, red testnet banner visible, status panel showing
  Mode / Network "Base Sepolia (testnet)" / Chain ID 84532.
- Action: none. Let the banner read.
- Say (over): "Every early-warning system has the same flaw: it never keeps score.
  Anyone can print a red alert. Nobody comes back a week later to say whether they were right."

## Shot 2 — 0:08–0:22 (14s) — What it does

- Screen: same dashboard.
- Action: click "Buy through Telegraph" (button id `buy`) with default query
  "Assess outbreak risk for dengue in Karachi". Wait for the settlement proof panel to appear.
- Say (over): "Outbreak Sentinel fixes that. It fuses news, weather, and social chatter
  with an LLM into a calibrated risk card — and only when two independent signal families
  agree. Then it issues a signed receipt: the sha256 of the card, appended to an immutable ledger."

## Shot 3 — 0:22–0:37 (15s) — Why Telegraph gave it an edge

- Screen: zoom/crop settlement proof panel: Miner, Amount (USD), Sepolia tx hash, clickable link, Network label, Mode.
- Action: click the clickable tx link once (opens sepolia.basescan.org/tx/<hash>) — cut back to dashboard.
  Optional second window: http://localhost:8000/telegraph/intents showing `"count": 134`.
- Say (over): "New this build: it does not call APIs directly. It buys ranked intelligence
  through Telegraph — parallel paid requests, each routed to the highest-ranked miner, each
  returning a receipt. Settlement on Base Sepolia. The money is on screen: miner, amount,
  tx hash, network."

## Shot 4 — 0:37–0:50 (13s) — The moat

- Screen: new tab http://localhost:8000/scoreboard, then http://localhost:8000/receipts.
- Action: point cursor at `receipt_id` (`rcpt-9575593f78c6`), `content_hash`, `status: "OPEN"`.
- Say (over): "A week later we resolve the receipt against a real source — confirmed or
  refuted. The scoreboard is the honest track record. 'Trust our AI' becomes 'check our ledger.'"

## Shot 5 — 0:50–0:60 (10s) — Close

- Screen: terminal `ls verticals/` (7 files) or `verticals/README.md` template.
- Action: none.
- Say (over): "Seven verticals, one engine. Add yours in fifty lines. Check our ledger."

---

## Cut list (if you run long)

Drop in this order: intents count (Shot 3), scoreboard tab (Shot 4 keep receipts only),
verticals template detail (Shot 5 keep `ls` only). Never cut the testnet banner or the tx hash.

## Do not

- Do not hide the "MOCKED settlement" label — it must be visible. Judges check for honesty.
- Do not record a real Sepolia tx as if live; settlement is mocked (Mechanism build) and the hash is synthetic. Say so if asked.