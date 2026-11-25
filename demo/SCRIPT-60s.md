# 60-Second Judge Demo — Outbreak Sentinel (Telegraph S2 · Track 01 — Apps & Agents)

Beat sheet for the v5 Operations Console. **SAY lines are verbatim** — read them as written.
~155 words at 150 wpm ≈ 60s. `[SCREEN]` = what the judge must actually see.

- Open (live): `https://outbreak-sentinel.onrender.com/telegraph/dashboard` — full-screen, SIMPLE mode, feed already streaming.
  Free tier sleeps after ~15 min idle; wake it with one `/health` hit and wait ~50 s before recording.
- Run it locally instead: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001`
  → `http://127.0.0.1:8001/telegraph/dashboard`
- Pre-load once before recording so the `SETTLED ON-CHAIN` strip already shows the seeded tx if the live call stalls.

---

## 0:00–0:05 — Hook (1 sentence)

**[SCREEN]** Console loaded; header, `engine: deterministic+narrator` badge (or `deterministic`), testnet banner all visible. Cursor still.

**SAY:** "These risk cards are free — news, weather and social signals scored in code. The paid ask is what settles on-chain, and its answer becomes a cited driver right here."

## 0:05–0:15 — Problem (fragmentation, no provenance)

**[SCREEN]** Hover three feed items in the left column; point at the news / weather / social family chips.

**SAY:** "Outbreak warnings arrive as scattered news, weather and social posts — no provenance, and no score kept. You cannot tell a real signal from a loud one."

## 0:15–0:24 — The ask (query, city, disease, buy)

**[SCREEN]** Click the query field: `dengue outbreak risk Karachi`. City `Karachi`, disease `dengue`.
Hover **Buy through Telegraph**, click once. Button changes to `Settling…`.

**SAY:** "So I ask one question — dengue risk in Karachi. I pick city and disease, and the agent buys ranked intelligence through Telegraph."

## 0:24–0:35 — LIVE SETTLEMENT PROVEN (the proof beat)

**[SCREEN]** When the green `LIVE SETTLEMENT PROVEN` chip lands, the `SETTLED ON-CHAIN` strip shows the
new tx hash. Click the explorer link → `sepolia.basescan.org/tx/<hash>`.
**Read the block number aloud from that explorer page** — never from this script; it is the block of the tx that just landed.

**SAY:** "That is a real Base Sepolia transaction — so the paid intelligence is notarized before anyone can edit it, and its answer is now the first driver on this card."

## 0:35–0:50 — Product breadth (same console, more surface)

**[SCREEN]** Back to the console. Scroll cards: `PAKISTAN` header, then `OTHER CITIES`. Point at the engine
badge, a citation chip, the AI summary line, a card-foot `rain forecast · 7d` strip. Toggle `SIMPLE → PRO` and hold on
PRO rows (miner, micro-units, scheme, block), then toggle back.

**SAY:** "Same console, grouped Pakistan and other cities; the engine behind it carries ten-plus cities across three live verticals — bio, wildfire and supply-chain — with cited sources, AI summaries and a rain-forecast strip. Flip SIMPLE to PRO for miner, micro-units, scheme and block."

## 0:50–0:60 — Close (ledger moat + call to action)

**[SCREEN]** Stay on the PRO receipt: tx strip, block, receipt hash. Nothing else moves.

**SAY:** "Every HIGH or CRITICAL call gets a receipt we resolve later — confirmed or refuted. 'Trust our AI' becomes 'check our ledger'."

---

## Fallback — settlement runs past 40s

Do **not** cut away and do **not** improvise a hash. Hold the panel, narrate the wait:

**SAY:** "While the agent waits on settlement, watch the free grid — news, weather and social, all cited."

Then resume at 0:35. If the chip lands while you talk, go back to the 0:24 beat.

## Hard rules

- Every hash on screen must be one the console actually returned; read the block from the explorer page, not from a script.
- **1 cent** is the price of a **paid ask only** — the 34-card grid costs nothing. Never say every prediction was paid.
- Testnet is stated out loud once. Never imply mainnet, and never call the console a mock.
- No accuracy percentages, no "revolutionary", no "unicorn".
- If asked "is this real money?" — "Base Sepolia testnet USDC; the settlement rail is live, the chain is not mainnet."
