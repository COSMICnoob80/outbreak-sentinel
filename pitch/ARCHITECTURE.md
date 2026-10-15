# Architecture — one engine, a vertical seam, a signed ledger

The point of this diagram is the **seam**: everything above the line is
domain-agnostic and never changes; everything below the line is a vertical, and
swapping it is a config change.

```
                                   ┌───────────────────────────────────────────┐
                                   │              VERTICALS  (the seam)         │
                                   │  bio-surveillance │ wildfire │ supply-chain │
                                   │  (+ yours in ~50 lines)                    │
                                   └───────────────────────┬───────────────────┘
                                            Vertical.to_config()
                                                           │
    ┌──────────────────────────────────────────────────────▼───────────────────┐
    │                        CORE ENGINE  (domain-agnostic)                     │
    │                                                                          │
    │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                  │
    │   │ SIGNAL       │   │ SIGNAL       │   │ SIGNAL       │   ── adapters ──▶│
    │   │ SOURCES      │   │ SOURCES      │   │ SOURCES      │                  │
    │   │ news (RSS)   │   │ weather      │   │ social       │                  │
    │   │              │   │ (Open-Meteo) │   │ (chatter)    │                  │
    │   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                  │
    │          └──────────────┬───┴──────────────────┘                          │
    │                         ▼                                                 │
    │                 ┌───────────────┐                                         │
    │                 │  FUSION       │  Groq LLM  ── role + thresholds          │
    │                 │  (per loc.)   │  from the active Vertical                │
    │                 └───────┬───────┘                                         │
    │                         ▼  rule-based fallback if LLM unavailable         │
    │                 ┌───────────────┐                                         │
    │                 │  RISK CARD    │  level · confidence · numeric drivers   │
    │                 │  (calibrated) │  HIGH requires >=2 independent families │
    │                 └───────┬───────┘                                         │
    │                         ▼                                                 │
    │                 ┌───────────────┐   sha256 content-hash id                │
    │                 │ RECEIPT LEDGER│   append-only history/receipts.jsonl    │
    │                 │ (tamper-evident)│  OPEN ──resolve──▶ CONFIRMED/REFUTED   │
    │                 └───────┬───────┘                                         │
    │                         ▼                                                 │
    │                 ┌───────────────┐                                         │
    │                 │  SCOREBOARD   │  calls made · resolved · verdicts       │
    │                 └───────┬───────┘                                         │
    └─────────────────────────┼──────────────────────────────────────────────┘
                              ▼
              ┌───────────────────────────────────────────────┐
              │            CHANNEL ADAPTERS  (delivery)        │
              │   console · FastAPI JSON · SMS / WhatsApp /    │
              │   email / webhook   ── swap per track ──       │
              └───────────────────────────────────────────────┘
```

## The two seams

**1. Vertical seam (above the line).** A `Vertical` (`verticals/base.py`) declares
`signal_sources`, `forecast_vars`, `keywords`, `locations`, and a `RiskModel`
(`high_means`, `escalation_rule`, `downgrade_rule`). `Vertical.to_config()`
compiles it into the dict the engine's `load_config()` already reads
(`cities`, `diseases`, `news_keywords`, `social_keywords`, `lookback_hours`).
Adding a domain touches **no** engine file.

**2. Channel seam (below the line).** The ledger is the source of truth; delivery
is an adapter. The console and the FastAPI JSON API ship today. An SMS/WhatsApp
adapter is what a cloud/communications track plugs in — the engine is unchanged.

## What is universal vs. what is per-vertical

| Layer | Universal (engine) | Per-vertical (config) |
|---|---|---|
| Signal fetch | fetcher code | which sources + keywords |
| Weather vars | request machinery | `forecast_vars` (temp/rain vs wind/humidity) |
| Fusion persona | LLM call + JSON contract | `fusion_role` + `RiskModel` text |
| Calibration | ≥2-signal rule enforced | what `HIGH` *means* |
| Ledger | hash, append, resolve | the subject axis ("disease"/"hazard"/"disruption") |
| Delivery | adapter interface | channel choice |

## Receipt lifecycle

```
   make_receipt(payload)                store.append()               store.resolve()
   ────────────────────────             ──────────────               ──────────────
   canonical JSON (sorted keys)         idempotent by id             appends resolve event
   sha256 → content_hash                JSONL line, never rewritten  status OPEN → RESOLVED
   receipt_id = rcpt-<hash[:12]>        status = OPEN                resolution = {verdict, source}
```

Truth lives in the ledger's *events*, not in any mutable field: a resolution is a
new line, so the audit trail is intact even after a call is scored. That is the
property that makes the scoreboard believable.

## Files

```
verticals/          the seam: base.py + 3 verticals + registry
outbreak_sentinel.py  the engine (fusion, rule-based fallback, card output)
receipts.py         ledger: make_receipt / ReceiptStore (append, resolve)
publish.py          HIGH/CRITICAL cards → receipts
verify.py           human resolver: CONFIRMED / REFUTED + source
app.py              FastAPI: /risk /receipts /receipts/{id} /scoreboard
agents/             the studio-team pattern (director, signal architect, ...)
pitch/              this kit
```
