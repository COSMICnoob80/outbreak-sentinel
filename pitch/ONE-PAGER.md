# Outbreak Sentinel — the agentic early-warning platform with a verifiable prediction ledger

> **We don't just alert. We issue a signed prediction and later prove whether we were right.**

*(The name reflects our first vertical — bio-surveillance. The platform is vertical-agnostic.)*

## The problem

Early-warning systems are cheap to build and impossible to trust. Anyone can
print a red banner. Nobody keeps score. An alerting system that never resolves
its own calls is indistinguishable from a spam filter, so responders learn to
ignore it — and the one real signal gets missed with the fake ones.

## What it does

Outbreak Sentinel runs a single loop:

```
open signals ─→ fuse with an LLM ─→ calibrated risk card ─→ signed receipt ─→ resolve vs reality
```

1. **Collect** open signals for a set of locations — news, weather forecast, and
   social chatter from free sources.
2. **Fuse** them with an LLM into one card per location: a risk level, a
   confidence, and the *numeric drivers* behind them.
3. **Constrain** the card with a calibration rule: `HIGH` requires ≥ two
   *independent* signal families to agree. One signal is never enough.
4. **Issue a receipt** — every `HIGH`/`CRITICAL` card is hashed (sha256) and
   appended to an immutable ledger. The id derives from the content, so the same
   input is idempotent and the receipt cannot be rewritten after the fact.
5. **Resolve** it later against an official source: `CONFIRMED` or `REFUTED`.
   Resolution appends a new event — history is never mutated.
6. **Score** it. The `/scoreboard` endpoint is the honest track record: calls
   made, calls resolved, verdicts. This is the part nobody else ships.

## The moat: the receipt ledger

The differentiator is not the LLM and not the data — both are commodities. It is
**accountability**. A receipt is a falsifiable public claim:

- **Tamper-evident** — content-hash id, append-only JSONL, no rewrite helper.
- **Resolvable** — a human confirms or refutes it against a real source.
- **Auditable** — the ledger *is* the resume. You can read every call we made
  and whether we were right.

That turns "trust our AI" into "check our ledger" — the only thing that makes an
early-warning system worth acting on.

## One engine, many verticals

The engine never changes. A **vertical** is a ~50-line declarative config: what
to watch, which signals, how to read the weather, and *what `HIGH` means*.

| Vertical | Watches | Signals | `HIGH` means |
|---|---|---|---|
| Bio-surveillance | Cities, diseases | news + weather + social | outbreak likely within 7d |
| Wildfire | Fire-prone regions | news + weather (wind, humidity) | fast-spreading fire within 48h |
| Supply chain | Trade hubs | news + weather + social | hub disruption within 7d |
| *yours* | *anything* | *any signal set* | *you write the contract* |

Same fusion, same ledger, same resolution loop. Add a vertical, get the whole
apparatus for free. (`verticals/README.md` has the ≤50-line recipe.)

## Live demo

- `GET /risk` — fresh fused risk cards (real Groq LLM fusion on `openai/gpt-oss-120b`).
- `GET /receipts` — the append-only ledger of issued calls.
- `GET /scoreboard` — `total_receipts`, `resolved`, verdict counts.
- `python verify.py <id> CONFIRMED "<source>"` — resolve a call against reality.
- `GET /receipts/{id}` — a single tamper-evident receipt.

## Stack & cost

Python · FastAPI · Groq LLM (free tier) · Open-Meteo + Google News RSS ·
append-only JSONL ledger · Railway / Oracle Always Free. **$0/month.**

## Why it fits your track

- **Health / bio hackathons** — a real disease-surveillance vertical, ready now.
- **Cloud hackathons** — the receipt ledger + agent orchestration as a
  delivery channel; ship cards out over SMS/WhatsApp/email adapters.
- **Agentic-AI hackathons** — an agent team (`agents/`) plus the studio pattern
  and a verified prediction ledger.
- **Data / infra hackathons** — calibration, a false-positive budget, and an
  auditable, append-only ledger with a resolution protocol.

Same repo, same demo, four stories — because the moat is the loop, not the label.
