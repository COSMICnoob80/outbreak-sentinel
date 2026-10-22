# Outbreak Sentinel — Telegraph Hackathon S2 submission

Track 03 · agentic commerce · Base Sepolia testnet

## What it is

An autonomous early-warning agent that buys ranked intelligence through Telegraph over x402 and fuses it with news, weather and social signals into calibrated outbreak risk cards. Every paid assessment is notarized by a real on-chain settlement and filed as a receipt that is later resolved CONFIRMED or REFUTED, so the product ships a track record instead of a claim.

## Demo

- URL: `http://127.0.0.1:8001/telegraph/dashboard`
- Run: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001`
- Walkthrough: `demo/SCRIPT-60s.md` · capture plan: `demo/SHOTLIST.md`
- No public deployment is claimed. Railway/Docker configs exist in-repo; the verified environment is the local server above.

## Judging map

| Likely criterion | What answers it |
|---|---|
| Agentic autonomy | one `POST /telegraph/risk` runs the whole loop — miner discovery via `/telegraph/intents` (134 intents), intent routing, payment, settlement, LLM fusion — no human step between query and card |
| x402 protocol usage | live 402 challenge → exact-scheme accept selection on `eip155:84532` → EIP-3009 authorized transfer via the facilitator; proof returns `settlement.mocked=false` and `rail="x402 (live)"` |
| Real settlement | three verified Base Sepolia transactions at 0.01 USDC each: `0x3825fa28…` (block 48410853), `0xfbfe793e…` (block 48407506), `0xf2276f58…`; checked independently with `eth_getTransactionByHash` |
| UI/UX | v5 console: PAKISTAN/GLOBAL grouping, per-item signal scores, always-on sparklines, cited sources, AI summaries, one SIMPLE/PRO chain toggle |
| Usefulness | built by an MBBS: outbreak chatter precedes official confirmation, and the receipt ledger makes each call falsifiable with a public scoreboard |
| Honesty posture | testnet boundary stated unprompted in UI, API and docs; static data labelled whenever live fusion is not what is on screen |

## Limitations (plain)

- **Testnet, not mainnet.** Settlement runs on Base Sepolia (chain 84532) in testnet USDC: 0.01 USDC per ask, 19.97 USDC left on burner `0x7b3654…`. Mainnet is a config change, not a claim.
- **Ingestion is RSS-based.** News and the "social" signal both come from Google News RSS; weather from Open-Meteo. No direct X access, so social is a proxy and is labelled as one.
- **Backend is a local dev server.** uvicorn bound to 127.0.0.1 serves the API and console; the Docker/Railway path is configured but is not the verified deployment.
- **LLM fusion is non-deterministic.** Card counts and levels vary per run (5–8 cards observed); `/risk` exposes no numeric score, so the console's big number is a level-band + confidence index and mini-sparklines say when they are calibration data.
- **Surveillance, not diagnosis.** Cards are cited early-warning signals. No treatment guidance, no personal health data.
