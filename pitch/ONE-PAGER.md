# Outbreak Sentinel — agentic early warning with a verifiable prediction ledger

> **We don't just alert. We issue a signed prediction and later prove whether we were right.**

*(The name reflects our first vertical — bio-surveillance. The platform is vertical-agnostic: seven verticals are registered as configs, three render live cards today — bio-surveillance, wildfire and supply-chain.)*

## The problem

Early-warning systems are cheap to build and impossible to trust. Anyone can
print a red banner. Nobody keeps score. An alerting system that never resolves
its own calls is indistinguishable from a spam filter, so responders learn to
ignore it — and the one real signal gets missed with the fake ones.

## What it does

```
open signals ─→ deterministic score ─→ LLM narrates ─→ calibrated risk card ─→ signed receipt ─→ resolve vs reality
```

1. **Collect** open signals for a set of locations — news, weather forecast, social chatter.
2. **Score** them deterministically into one card per location: risk level, confidence, numeric drivers, 0–100 score. The LLM never chooses the level — it only narrates the card it is handed.
3. **Constrain** the card: a city with no city-named report is capped at `LOW` and confidence ≤ 0.55. An unwitnessed outbreak never gets a confident card.
4. **Issue a receipt** — every `HIGH`/`CRITICAL` card is sha256-hashed and appended to an immutable ledger.
5. **Resolve** later against a real source: `CONFIRMED` or `REFUTED`. Resolution appends a new event; history is never mutated.
6. **Score** it via `/scoreboard`: calls made, resolved, verdicts. `resolved: 0` means "not yet checked," not "hidden."

## Moat 1 — the receipt ledger

The differentiator is not the model and not the data — both are commodities. It is
**accountability**. A receipt is a falsifiable public claim: content-hash id,
append-only JSONL, no rewrite helper, human resolution against a real source.
That turns "trust our AI" into "check our ledger."

## Moat 2 — the agent buys intelligence (Telegraph)

New this build: the agent does not call APIs directly. It buys *ranked*
intelligence through Telegraph — a paid request routed to a miner and settled
live over x402 on Base Sepolia testnet. The money is first-class JSON and on
screen: miner, amount, tx hash, network label, plus a clickable Sepolia explorer
link and an on-screen testnet boundary statement. The purchased answer is a
**cited driver on the resulting card**, so the buy → card chain is visible in the
response and on the console. Mainnet flip is a config change, not a code change.

## One engine, seven verticals — three live today

The engine never changes. A vertical is a ~50-line declarative config: what to
watch, which signals, how to read the weather, and *what `HIGH` means*.

Registered: bio-surveillance · pandemic · endemic · wildfire · supply-chain ·
commodity-disruption · financial-stress.
Rendering live cards on `/risk` today: **bio-surveillance · wildfire · supply-chain**.
The rest are config-only and produce no cards yet.

Same scoring, same ledger, same resolution loop. Add a vertical, get the whole
apparatus free. (`verticals/README.md` has the ≤50-line recipe.)

## Live demo

- `https://outbreak-sentinel.onrender.com/telegraph/dashboard` — live console, testnet banner unprompted.
- `POST /telegraph/risk` — paid request → ranked answer (cited as a card driver) + settlement proof + risk card.
- `GET /telegraph/status` — mode / network / chain / boundary / last settlement (seeded from the ledger on restart).
- `GET /telegraph/intents` — live miner discovery (~136 intents).
- `GET /risk`, `/receipts`, `/receipts/{id}`, `/scoreboard`, `/cities`, `/diseases`.
- `GET /intel/llm` — provider proof: `{"provider":"commandcode","ok":true}`.
- `python verify.py <id> CONFIRMED "<source>"` — resolve a call against reality.

## Stack & cost

Python · FastAPI · deterministic scoring engine with a narrator-only LLM
(Command Code provider, `z-ai/glm-5.3-flash`; Groq optional fallback) ·
Open-Meteo + Google News RSS · append-only JSONL ledger · Telegraph buying layer
(Base Sepolia) · Render blueprint. **$0/month.** Full test suite green.

## Why it fits your track

- **Health / bio** — a real disease-surveillance vertical, live today, surveillance not diagnosis.
- **Agentic AI** — an agent team (`agents/`) plus a verified prediction ledger.
- **Cloud / communications** — receipt ledger + delivery adapters (console/webhook/file, `POST /alerts`).
- **Data / infra** — calibration, a false-positive budget, an auditable append-only ledger with a resolution protocol.

Same repo, same demo — because the moat is the loop, not the label.
