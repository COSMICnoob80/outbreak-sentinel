# HARVEST — Telegraph S1 Apps/Agents track winners (Scam Shield + Truvian Shield)

Date: 2026-11-01 · Channel: `public web app (live DOM inspection + rendered screenshots, screenshots in ~/.hermes/cache/scratch/harvest-*.png)`
Targets: https://scam-shield-rouge.vercel.app/ (1st, 0.69), https://truvian.xyz/ (2nd, 0.59). ProofPact (3rd, 0.45) not directly inspected — majors read from the winners page only.

## Evidence table

| # | Finding | Channel | Source |
|---|---------|---------|--------|
| E1 | One-verb hero: "Paste it → It fans out → One verdict, fully shown." One input (textarea), one output (verdict sentence). | public web app | Scam Shield / and /check |
| E2 | Tiered spend limiter: Essentials (~$0.50) / Standard / Thorough chips control how much the app pays for a check. | public web app | Scam Shield /check |
| E3 | Sample-case buttons pre-fill the input: "Fake delivery text", "Phishing email", "Legitimate newsletter" — judges get a demo in one click. | public web app | Scam Shield /check |
| E4 | Verdict is one plain sentence, explicitly NOT a percentage ("A verdict, not a score"). | public web app | Scam Shield landing |
| E5 | Multi-miner fan-out with graceful degradation: 23 miners, 9 intents; "when a miner errors or times out mid-scan, the check continues without it". Redundancy IS the design. | public web app | Scam Shield landing |
| E6 | Public ledger page: every scan listed (time, input, verdict, miner-call count, cost), KPI strip on top (41 scans / 492 calls / 20 miners / $2.43 spent / 4 scam–26 suspicious–11 clean). Honest "inconclusive" verdicts shown. | public web app | Scam Shield /ledger |
| E7 | Trust copy: "Every check is a real payment to an independent miner — not a cached answer." + "Paid, not guessed." | public web app | Scam Shield footer/landing |
| E8 | Free during early access; pricing page shows the future token plan. Removes the payer-friction objection from judges. | public web app | Scam Shield /pricing |
| E9 | API-first positioning: "One POST before the signature: four paid questions … one verdict, receipts anyone can verify." Judges saw their OWN agents as the customer. | public web app | Truvian landing |
| E10 | Deterministic public scoring: start at 100; −15 warn / −35 fail / −10 error; ≥80 SAFE, 50–79 CAUTION, <50 BLOCK; "any fail ⇒ at most CAUTION; two fails ⇒ BLOCK". Published constants = same evidence, same verdict, every time. | public web app | Truvian #scoring |
| E11 | Per-intent cost table: each check named, which miner answers, when it runs, thresholds (e.g. "warn · > $10,000"). | public web app | Truvian #checks |
| E12 | Live spend telemetry: "10 checks run · 29 Telegraph requests · $0.29 paid to miners · funded for 445 more checks — live · GET /api/stats". Numbers pull live from the running system. | public web app | Truvian landing |
| E13 | Payment anatomy diagram: agent → 402 → EIP-3009 signature → Base settlement → signal_hash, rendered in plain steps a non-crypto judge can follow. | public web app | Truvian #architecture |
| E14 | Zero-jargon hero for judges: "$0.01 per miner query · ~10 s · 100% live miners" strip above the fold. | public web app | Truvian landing |
| E15 | S1 judge motivation (winners page): Scam Shield won for "multiple real user surfaces" (browser extension in Gmail + mobile SMS app) — the web app alone was NOT the differentiator. | public docs | hackathon.telegraphprotocol.com/winners |

## Adopted (build into Outbreak Sentinel v6 "second surface")

- A1 (E1,E3): `/telegraph/assess` — one text input + city field, sample-case chips pre-filled (malaria Ludhiana, dengue Karachi, measles US).
- A2 (E2): tier chips Essentials $0.01 / Standard $0.02 / Thorough $0.05 driving `amount_uusdc` 10000/20000/50000 on POST /telegraph/risk.
- A3 (E4,A4): verdict = first sentence of the engine summary + plain action line; severity chip; NO composite score shown on the simple tier.
- A4 (E6): `/telegraph/ledger` — public page listing every settlement receipt (time, city/disease, verdict, cost, explorer tx link) with KPI strip (assessments / total paid / integrity / verdict distribution). Honest "inconclusive"/low-confidence labels allowed.
- A5 (E10): publish the deterministic grading band constants from the rule-based fallback on the assess page footer ("our published thresholds") — same evidence, same verdict framing.
- A6 (E12): live telemetry line on the console: assessments run · tx count · total USDC spent · remaining wallet balance.

## Structurally excluded (reference platform teaches nothing here)

- X1: Scam Shield's message-scanning domain and its extension/SMS surfaces (their app-store distribution is not portable to our domain; we keep PWA-only for S2 — E15 remains a roadmap item, not a Nov deliverable).
- X2: Truvian's gas/tx/TVL check intents (DeFi-checkout domain).
- X3: Scam Shield's pricing/token-plan model (prepaid demo policy adopted instead: S2 submissions prepaid by us, mirroring E8).

## Absence row (the moat)

- (absence) No S1 app connects purchased intelligence to an outbreak/public-health risk card. No S1 app leads the user from a paid receipt to a full explorer transaction on a city assessment. Scam Shield shows signal hashes; we show full tx hashes with amounts — the receipt ledger for public-health decisions is unclaimed territory.
- (absence) No S1 app has a deterministic published-grading fallback tied to paid LLM assessment (Truvian has published grading but all four checks are miner calls; we run LLM-first with rule-based as labeled fallback — a two-engine honesty story none of them ships).

## Non-goals for the builder soldier

Do NOT adopt: message/forum scanning, anything requiring app stores, auth flows, real-money (non-testnet) payments, CDN assets, or renaming existing routes (`/telegraph/dashboard` stays; assess/ledger are additive).
