# Hackathon State — OUTBREAK SENTINEL

**Short status stub.** The authorities are `SPINE.md` (project state, checkpointed) and
`docs/AUDIT-2026-11-22.md` (objective readiness audit). This file is neither — it is a
one-screen summary kept in sync with them. If they disagree, they win.

- Updated: 2026-11-23
- Event: **Telegraph Hackathon Season II** (Nov 1 – **Dec 1, 2026, 23:59 UTC**)
- Deadline: **2026-12-01 23:59 UTC**
- Track: **Track 01 — Apps & Agents**
- Missions: **06 — Resources and Agriculture (days-to-impact per site)** and
  **11 — Autonomous Systems (autonomous units buying fire-risk answers)**
- Live instance: https://outbreak-sentinel.onrender.com
  (console `/telegraph/dashboard` · `/health` · `/receipts` · `/telegraph/status` · `/telegraph/stats`)
- Fallback event: Agentware (Nov 27–30) — see `pitch/AGENTWARE-BRIEF.md`

## Judging rubric (official)

35% technical / 25% commercial viability / 10% adoption / 5% integration /
5% reproducibility / 20% organic growth. Any other weights in older notes are wrong.

## Settlement state

- Rail: x402 on **Base Sepolia (chain 84532)**, **0.01 USDC** per paid ask, `settlement_mode: live`.
- Burner: `0x7b3654…f249`.
- Verified transactions (all 10,000-unit USDC `Transfer`s):
  <!-- block values copied from eth_getTransactionReceipt on Base Sepolia 2026-11-26T12:26:38Z -->
  - `0x979515ea…7067` — block **61,335,917**
  - `0xac02bcbb…c4cf` — block **59,597,289** (latest persisted row in `state/settlements.jsonl`)
  - `0xf2276f58…97d4` — block **48,407,418**
- `/telegraph/status` seeds the newest settled tx from `state/settlements.jsonl` on a fresh
  boot, so the proof is visible without spending.

## Ledger state

- `history/receipts.jsonl` is an append-only JSONL ledger; a HIGH/CRITICAL card that finalizes
  files exactly one receipt (id = hash of the claim), and `verify.py` resolves it later.
- `/scoreboard` reports receipts filed and how many are resolved. `resolved: 0` means
  "not yet checked", not "hidden".

## Verticals that actually render

bio-surveillance · wildfire · supply-chain (three). The other registered verticals are
config-only and produce no cards.
