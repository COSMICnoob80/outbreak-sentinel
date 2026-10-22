# 60-Second Judge Demo — Outbreak Sentinel (Telegraph S2 · Track 03)

Beat sheet for the v5 Operations Console. **SAY lines are verbatim** — read them as written.
~155 words at 150 wpm ≈ 60s. `[SCREEN]` = what the judge must actually see.

- Start: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001`
- Open: `http://127.0.0.1:8001/telegraph/dashboard` — full-screen, SIMPLE mode, feed already streaming.
- Pre-load once before recording so a real tx hash is on screen if the live call stalls.

---

## 0:00–0:05 — Hook (1 sentence)

**[SCREEN]** Console loaded; header, `engine: llm` badge, testnet banner all visible. Cursor still.

**SAY:** "Every outbreak prediction here cost 1 cent and is notarized on-chain — tamper-proof."

## 0:05–0:15 — Problem (fragmentation, no provenance)

**[SCREEN]** Hover three feed items in the left column; point at the news / weather / social family chips.

**SAY:** "Outbreak warnings arrive as scattered news, weather and social posts — no provenance, and no score kept. You cannot tell a real signal from a loud one."

## 0:15–0:24 — The ask (query, city, disease, buy)

**[SCREEN]** Click the query field: `dengue outbreak risk Karachi`. City `Karachi`, disease `dengue`.
Hover **Buy through Telegraph**, click once. Button changes to `Settling…`.

**SAY:** "So I ask one question — dengue risk in Karachi. I pick city and disease, and the agent buys ranked intelligence through Telegraph."

## 0:24–0:35 — LIVE SETTLEMENT PROVEN (the proof beat)

**[SCREEN]** ~24s later the green `LIVE SETTLEMENT PROVEN` chip lands; `SETTLED ON-CHAIN` strip shows
`0x3825fa28…`. Click the explorer link → `sepolia.basescan.org/tx/0x3825fa28…`.
**Read the block number aloud** — it is on the explorer page: **48,410,853**.

**SAY:** "Twenty-four seconds later: LIVE SETTLEMENT PROVEN. That is a real Base Sepolia transaction — block 48,410,853 — so the prediction is notarized before anyone can edit it."

## 0:35–0:50 — Product breadth (same console, more surface)

**[SCREEN]** Back to the console. Scroll cards: `PAKISTAN` header, then `GLOBAL`. Point at the engine
badge, a citation chip, the AI summary line, a card-foot sparkline. Toggle `SIMPLE → PRO` and hold on
PRO rows (miner, micro-units, scheme, block), then toggle back.

**SAY:** "Same console, grouped Pakistan and Global; the engine behind it carries ten-plus cities across seven verticals, with cited sources, AI summaries and sparklines. Flip SIMPLE to PRO for miner, micro-units, scheme and block."

## 0:50–0:60 — Close (ledger moat + call to action)

**[SCREEN]** Stay on the PRO receipt: tx strip, block, receipt hash. Nothing else moves.

**SAY:** "Every prediction gets a receipt we resolve later — confirmed or refuted. 'Trust our AI' becomes 'check our ledger' — and the burner still holds 19.97 USDC."

---

## Fallback — settlement runs past 40s

Do **not** cut away and do **not** improvise a hash. Hold the panel, narrate the wait:

**SAY:** "While the LLM fuses 60+ signals live — watch the feed."

Then resume at 0:35. If the chip lands while you talk, go back to the 0:24 beat.

## Hard rules

- Numbers only as written here: block **48,410,853**, **0x3825fa28…**, **19.97 USDC**, **~24s**, **1 cent**.
- Testnet is stated out loud once. Never imply mainnet, and never call the console a mock.
- No accuracy percentages, no "revolutionary", no "unicorn".
- If asked "is this real money?" — "Base Sepolia testnet USDC; the settlement rail is live, the chain is not mainnet."
