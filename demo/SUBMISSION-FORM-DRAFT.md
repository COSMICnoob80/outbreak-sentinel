# Telegraph Hackathon Season II — Submission Form Draft
(Drafted 2026-11-26 for COSMICnoob80. Paste each field into the form at
hackathon.telegraphprotocol.com — every claim below is verified against the
live deployment and docs/AUDIT-2026-11-26-final-gate.md.)

---

**Project name:** Outbreak Sentinel

**Track:** Track 01 — Apps & Agents

**Missions:** 06 (Resources & Agriculture — days-to-impact early-warning) and
11 (Autonomous Systems — an autonomous unit buying fire-risk intelligence)

**One-liner:** An autonomous early-warning agent that fuses open news,
weather and social signals into calibrated city risk cards, issues
tamper-evident receipts, and PAYS for deeper intelligence through the
Telegraph protocol — settling real x402 payments on Base Sepolia.

**What it does (plain words):**
Outbreak Sentinel watches 19 cities across 3 hazard verticals
(bio-surveillance, wildfire, supply-chain). It fuses Google News RSS, live
forecasts and social chatter into scored risk cards with cited sources — a
headline only counts as evidence if it names the hazard. When a card needs
deeper intelligence, the agent BUYS it: it routes a paid request through
Telegraph, answers the 402 challenge, signs an EIP-3009 transfer, and settles
real USDC on-chain — and the purchased answer is cited on the card as a
first-class driver. Every HIGH/CRITICAL card that finalizes gets a
tamper-evident receipt.

**Live deployment (judges, start here):**
- Console: https://outbreak-sentinel.onrender.com/telegraph/dashboard
  (free tier wakes in ~50 s; first render up to ~150 s, then cached 5 min)
- Health: https://outbreak-sentinel.onrender.com/health
- Receipts: https://outbreak-sentinel.onrender.com/receipts
- Settlement status: https://outbreak-sentinel.onrender.com/telegraph/status
- Public ledger: https://outbreak-sentinel.onrender.com/telegraph/ledger

**Demo video:** `demo/outbreak-sentinel-demo.mp4` in the repo — 3:52, 1920×1080,
captioned, built from the deployment's real captured API responses (rebuild
scripts included). Screenshots: `demo/screenshots/01…06.png`.

**Verified on-chain proof (checkable by anyone):**
<!-- copied from /telegraph/status 2026-11-26T12:26:38Z -->
tx 0xac02bcbbe78e85760f3ae45400d457f750c9f0fd61c0fc9d06189fe84aa9c4cf
<!-- block copied from eth_getTransactionReceipt on Base Sepolia 2026-11-26T12:26:38Z -->
status 0x1, block 59597289, 0.01 USDC, Base Sepolia —
<!-- link derived from the tx hash above; never retyped -->
https://sepolia.basescan.org/tx/0xac02bcbbe78e85760f3ae45400d457f750c9f0fd61c0fc9d06189fe84aa9c4cf
(Settlement mode: live; `mocked: false`; the settlement proof is seeded from
state/settlements.jsonl.)

**Telegraph integration specifics:**
- 402-challenge flow via TelegraphClient.buy_intelligence; settlement mode
  `live` (TELEGRAPH_SETTLEMENT_MODE=live) with a funded Base Sepolia burner.
- The engine quotes from the challenge, never a hardcoded price.
- Purchased `ranked_answer` is attached to the card as a cited `telegraph`
  driver (causal use, not a receipt for show).
- Resilience story for judges: Open-Meteo's shared-IP daily quota 429'd the
  host mid-competition; the agent ships a MET Norway fallback for that case —
  graceful degradation, not a dead panel. The video demonstrates it as a
  labelled replay of Render's verbatim 429, not an observed live serve.

**Integrity commitments a judge can falsify in 2 minutes:**
- Another disease's outbreak is never a card's evidence (disease-term gate;
  tests/test_disease_evidence.py, 193 lines).
- No synthetic sources anywhere; every card cites its real headlines.
- Suite: 125 passing tests; receipts dedupe by stable card identity.

**Repo:** https://github.com/COSMICnoob80/outbreak-sentinel
**GitHub username:** COSMICnoob80 (bounty repo starred from this account)

**Days-to-impact (Mission 06), stated honestly:** the evidence window is
7 days; a per-site spread/lead-time model is not in this build and we do not
claim one.

**What we did NOT build (so judges don't hunt for it):** per-site epidemic
spread modeling; a mobile app; mainnet settlement (testnet only, by design).

---

## The one action left (operator)
1. Star Telegraph's bounty repo from COSMICnoob80 on GitHub (30 s, phone).
2. Open the submission form, paste the fields above, attach/link the video.
3. Press submit BEFORE Dec 1, 23:59 UTC — then tell me; I log the send and
   update the board.
