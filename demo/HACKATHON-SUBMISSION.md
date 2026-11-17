# Outbreak Sentinel — Telegraph Hackathon S2 submission

Track 03 · agentic commerce · Base Sepolia testnet

## What it is

An autonomous early-warning agent that buys ranked intelligence through Telegraph over x402 and fuses it with news, weather and social signals into calibrated outbreak risk cards. Every card's city, disease, sources and 0–100 score are computed in code; the LLM is a narrator that may only write the summary and recommendation for the card it is handed — a deliberate strength, not a limitation. Every paid assessment is notarized by a real on-chain settlement and filed as a receipt that is later resolved CONFIRMED or REFUTED, so the product ships a track record instead of a claim.

## Demo

- Run locally: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001`
- Local URL: `http://127.0.0.1:8001/telegraph/dashboard`
- Tailnet URL (open tonight over Tailscale): `http://100.82.76.91:8001/telegraph/dashboard` — tailnet-only; the host machine must be awake and the server must listen on `0.0.0.0:8001` (add `--host 0.0.0.0` to the run command for tailnet access).
- Walkthrough: `demo/SCRIPT-60s.md` · capture plan: `demo/SHOTLIST.md`
- No public deployment is claimed. The Render blueprint (`render.yaml`, guide at `docs/DEPLOY-RENDER.md`) is configured in-repo; the verified environment is the local server above.

## Judging map

| Likely criterion | What answers it |
|---|---|
| Agentic autonomy | one `POST /telegraph/risk` runs the whole loop — miner discovery via `/telegraph/intents` (130+ live intents), intent routing, payment, settlement, deterministic scoring + LLM narration — no human step between query and card |
| x402 protocol usage | live 402 challenge → exact-scheme accept selection on `eip155:84532` → EIP-3009 authorized transfer via the facilitator; proof returns `settlement.mocked=false` and `rail="x402 (live)"` |
| Real settlement | three verified Base Sepolia transactions at 0.01 USDC each: `0x3825fa28…` (block 48410853), `0xfbfe793e…` (block 48407506), `0xf2276f58…`. All three hashes and blocks are recorded in `state/hackathon-state.md`; the full `0xf2276f58…` hash is in `SPINE.md` and resolves on Base Sepolia at block 48407418. Each opens at `sepolia.basescan.org/tx/<hash>` and can be checked with `eth_getTransactionByHash` |
| UI/UX | v5 console: `PAKISTAN` / `OTHER CITIES` grouping, feed rows showing `confidence 70%` (weather rows `peak 0 mm`), a labelled `rain forecast · 7d` strip that renders `no rain forecast` when every value is zero, cited sources, AI summaries, one SIMPLE/PRO chain toggle |
| Deterministic core | every card's city, disease, sources and 0–100 score are computed in code (score = city-specific reports over 7 days + rain + heat + concern); the LLM is a narrator that may only write the summary and recommendation for the card it is handed, and may move the level by at most one step — otherwise the prose is discarded |
| Usefulness | built by an MBBS: outbreak chatter precedes official confirmation, and the receipt ledger makes each call falsifiable with a public scoreboard |
| Honesty posture | testnet boundary stated unprompted in UI, API and docs; static data labelled whenever live fusion is not what is on screen |

## Limitations (plain)

- **Testnet, not mainnet.** Settlement runs on Base Sepolia (chain 84532) in testnet USDC: 0.01 USDC per ask, 19.95 USDC left on burner `0x7b3654…` (on-chain balance read 2026-11-17). Mainnet is a config change, not a claim.
- **Ingestion is RSS-based.** News and the "social" signal both come from Google News RSS; weather from Open-Meteo. No direct X access, so social is a proxy and is labelled as one.
- **Backend is a local dev server.** uvicorn bound to 127.0.0.1 serves the API and console; the Render blueprint path is configured but is not the verified deployment.
- **The grid is deterministic; only the prose is model-written.** The engine builds every card — city, disease, sources, 0–100 score, level, confidence — and labels itself `deterministic+narrator`. The score is city-specific reports over the last 7 days plus rain, heat and concern (the console prints the same `Score 0–100` footnote). The LLM writes only `summary` and `recommendation` for the card it is handed, and may move the level by at most one step; anything else (another city, another disease, an unsupplied source link, a numeric score, an extra field) is discarded and the deterministic prose stays. `/risk` exposes `risk_score` (0–100); a city with no city-named reports carries confidence ≤ 0.55 and cannot exceed `MODERATE` (`LOW` when the forecast is benign).
- **Surveillance, not diagnosis.** Cards are cited early-warning signals. No treatment guidance, no personal health data.
