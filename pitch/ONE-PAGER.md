# Outbreak Sentinel — agentic early warning with a verifiable prediction ledger

> **We don't just alert. We issue a signed prediction and later prove whether we were right.**

*(The name reflects our first vertical — bio-surveillance. The platform is vertical-agnostic: 7 verticals ship today.)*

## The problem

Early-warning systems are cheap to build and impossible to trust. Anyone can
print a red banner. Nobody keeps score. An alerting system that never resolves
its own calls is indistinguishable from a spam filter, so responders learn to
ignore it — and the one real signal gets missed with the fake ones.

## What it does

```
open signals ─→ fuse with an LLM ─→ calibrated risk card ─→ signed receipt ─→ resolve vs reality
```

1. **Collect** open signals for a set of locations — news, weather forecast, social chatter.
2. **Fuse** them with an LLM (Groq, free tier) into one card per location: risk level, confidence, numeric drivers.
3. **Constrain** the card: `HIGH` requires ≥ two *independent* signal families. One signal never escalates.
4. **Issue a receipt** — every `HIGH`/`CRITICAL` card is sha256-hashed and appended to an immutable ledger.
5. **Resolve** later against a real source: `CONFIRMED` or `REFUTED`. Resolution appends a new event; history is never mutated.
6. **Score** it via `/scoreboard`: calls made, resolved, verdicts. `resolved: 0` means "not yet checked," not "hidden."

## Moat 1 — the receipt ledger

The differentiator is not the LLM and not the data — both are commodities. It is
**accountability**. A receipt is a falsifiable public claim: content-hash id,
append-only JSONL, no rewrite helper, human resolution against a real source.
That turns "trust our AI" into "check our ledger."

## Moat 2 — the agent buys intelligence (Telegraph)

New this build: the agent does not call APIs directly. It buys *ranked*
intelligence through Telegraph — parallel paid requests, each routed to the
highest-ranked miner, each returning a receipt; settlement on Base Sepolia
testnet. The money is first-class JSON and on screen: miner, amount, tx hash,
network label, plus a clickable Sepolia explorer link and an on-screen testnet
boundary statement. The seam is real REST (miner discovery, ask, 402 challenge);
settlement is an honest Mechanism build (mocked, clearly labeled) until a
wallet is wired. Mainnet flip is a config change, not a code change.

## One engine, seven verticals

The engine never changes. A vertical is a ~50-line declarative config: what to
watch, which signals, how to read the weather, and *what `HIGH` means*.

bio-surveillance · pandemic · endemic · wildfire · supply-chain ·
commodity-disruption · financial-stress.

Same fusion, same ledger, same resolution loop. Add a vertical, get the whole
apparatus free. (`verticals/README.md` has the ≤50-line recipe.)

## Live demo

- `GET /telegraph/dashboard` — money-visible front end, testnet banner unprompted.
- `POST /telegraph/risk` — paid request → ranked answer + settlement proof + risk card.
- `GET /telegraph/status` — mode / network / chain / boundary / last settlement.
- `GET /telegraph/intents` — live miner discovery (134 intents).
- `GET /risk`, `/receipts`, `/receipts/{id}`, `/scoreboard`, `/cities`, `/diseases`.
- `python verify.py <id> CONFIRMED "<source>"` — resolve a call against reality.

## Stack & cost

Python · FastAPI · Groq LLM (free tier, `openai/gpt-oss-120b`) · Open-Meteo +
Google News RSS · append-only JSONL ledger · Telegraph buying layer (Base Sepolia)
· Railway / Oracle Always Free. **$0/month.** 3 tests passing.

## Why it fits your track

- **Health / bio** — a real disease-surveillance vertical, live today, surveillance not diagnosis.
- **Agentic AI** — an agent team (`agents/`) plus a verified prediction ledger.
- **Cloud / communications** — receipt ledger + delivery adapters (console/webhook/file, `POST /alerts`).
- **Data / infra** — calibration, a false-positive budget, an auditable append-only ledger with a resolution protocol.

Same repo, same demo — because the moat is the loop, not the label.