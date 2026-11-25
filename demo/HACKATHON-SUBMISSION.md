# Outbreak Sentinel — Telegraph Hackathon S2 submission

**Track 01 — Apps & Agents** · Base Sepolia testnet · **Missions 06 (Resources & Agriculture — days-to-impact) and 11 (Autonomous Systems — autonomous forestry units buying fire-risk)**

## What it is

An autonomous early-warning agent that buys ranked intelligence through Telegraph over x402 and fuses it with news, weather and social signals into calibrated outbreak risk cards. Every card's city, disease, sources and 0–100 score are computed in code; the LLM is a narrator that may only write the summary and recommendation for the card it is handed — a deliberate strength, not a limitation. The purchased answer is a **cited driver on the resulting card**, so the buy → card chain is visible in the response. Every paid assessment is notarized by a real on-chain settlement, and every HIGH/CRITICAL card that finalizes is filed as a receipt that is later resolved CONFIRMED or REFUTED, so the product ships a track record instead of a claim.

## Live demo

- **Console:** https://outbreak-sentinel.onrender.com/telegraph/dashboard
- **Health:** https://outbreak-sentinel.onrender.com/health
- **Receipt ledger:** https://outbreak-sentinel.onrender.com/receipts
- **Settlement status (chain / boundary / last settled tx):** https://outbreak-sentinel.onrender.com/telegraph/status
- **Settlement stats + public ledger page:** https://outbreak-sentinel.onrender.com/telegraph/stats · `/telegraph/ledger`

Free-tier instance: it sleeps after ~15 minutes idle and takes ~50 s to wake. The console's first `/risk` render can take up to ~150 s on a cold instance; the result is then cached for 5 minutes.

Run it locally if you prefer:

```
env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Walkthrough: `demo/SCRIPT-60s.md` · capture plan: `demo/SHOTLIST.md`

## Missions

- **06 — Resources and Agriculture.** The wildfire vertical answers "days-to-impact per site" from the agent's own signal stack: city-scoped wildfire reports over 7 days plus a dry/windy outlook, each card carrying its own evidence count, score and cited sources. The agent buys the matching intelligence through Telegraph and the answer becomes a cited driver on the card.
- **11 — Autonomous Systems.** An autonomous unit buying fire-risk answers: `POST /telegraph/risk` runs miner discovery → intent routing → x402 payment → settlement → card with no human step between query and result. The money is first-class JSON (miner, amount, tx hash, network label) and on screen.

## Judging map (official weights: 35 / 25 / 10 / 5 / 5 / 20)

| Weight | Criterion | What answers it |
|---|---|---|
| 35% | Technical / mainnet readiness | real 402 challenge → exact-scheme accept selection on `eip155:84532` → EIP-3009 authorized transfer via the facilitator; `settlement.mocked=false`, `rail="x402 (live)"`; deterministic scoring with a narrator limited to `summary`/`recommendation` and a ≤1-step level move |
| 25% | Commercial viability | `pitch/COMMERCIAL-SUMMARY.md` — buyer, what it replaces, unit economics (~$0.01 of Telegraph miner cost per paid assessment; free RSS + Open-Meteo signals), >90% gross-margin target |
| 10% | Adoption | self-serve surface (`/telegraph/assess`), public ledger (`/telegraph/ledger`), machine-readable API (`/risk`, `/telegraph/risk`) |
| 5% | Integration | Telegraph REST seam (miner discovery, ask, 402), our own FastAPI service, Render deploy, PWA console |
| 5% | Reproducibility | `env -u PYTHONPATH .venv/bin/python -m pytest -q` → 119 passed; `render.yaml` blueprint in-repo; run command above |
| 20% | Organic growth | dated public updates + an invitation to reproduce; every claim in this doc opens a URL a reviewer can check |

### Settlement evidence

Paid asks settle on **Base Sepolia (chain 84532)** at **0.01 USDC** each. Recent verified transactions:

- `0x979515ea…7067` — block **61,335,917**, USDC `Transfer` 10,000 units (0.01 USDC) from burner `0x7b36…f249`
- `0xac02bcbb…c4cf` — block **59,597,289**, 10,000 units, same burner
- `0xf2276f58…97d4` — block **48,374,650**, 10,000 units, same burner

Each opens at `sepolia.basescan.org/tx/<hash>` and can be checked with `eth_getTransactionByHash`. `/telegraph/status` returns the most recent settled tx on a fresh boot (seeded from `state/settlements.jsonl`), so the proof is visible without spending.

## Limitations (plain)

- **Testnet, not mainnet.** Settlement runs on Base Sepolia (chain 84532) in testnet USDC: 0.01 USDC per ask. Mainnet is a config change, not a claim.
- **The 34-card grid is free; the paid ask is what settles.** Refreshing `/risk` costs nothing and produces no transaction. Only `POST /telegraph/risk` spends, and that is the path whose answer becomes a cited driver and whose settlement is notarized.
- **Ingestion is RSS-based.** News and the "social" signal both come from Google News RSS; weather from Open-Meteo. No direct X access, so social is a proxy and is labelled as one.
- **Three verticals render today:** bio-surveillance, wildfire and supply-chain. The other registered verticals are config-only and produce no cards.
- **The grid is deterministic; only the prose is model-written.** The engine builds every card — city, disease, sources, 0–100 score, level, confidence — and labels itself `deterministic+narrator`. The score is city-specific reports over the last 7 days plus rain, heat and concern (the console prints the same `Score 0–100` footnote). The LLM writes only `summary` and `recommendation` for the card it is handed, and may move the level by at most one step; anything else (another city, another disease, an unsupplied source link, a numeric score, an extra field) is discarded and the deterministic prose stays. `/risk` exposes `risk_score` (0–100); a city with no city-named reports carries confidence ≤ 0.55 and cannot exceed `MODERATE` (`LOW` when the forecast is benign).
- **Receipts resolve forward.** A receipt is filed when a HIGH/CRITICAL card finalizes and is resolved later against a real source; `/scoreboard` shows how many are resolved. `resolved: 0` means "not yet checked", not "hidden".
- **Surveillance, not diagnosis.** Cards are cited early-warning signals. No treatment guidance, no personal health data.
