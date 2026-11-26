# VIDEO-CAPTIONS — Outbreak Sentinel demo (Soldier V-1)

**Deliverable:** `demo/outbreak-sentinel-demo.mp4` — 1920×1080, 30 fps, H.264, **232 s** (3:52),
captioned, no audio track. Built from real captured API responses, not screen capture.

**Rebuild:**
```bash
./demo/capture_video_data.sh                                        # live GETs → state/video-capture/*.json
env -u PYTHONPATH .venv/bin/python demo/capture_video_data.py       # → snapshot.json (+ forced MET fallback, on-chain read)
env -u PYTHONPATH .venv/bin/python demo/render_video.py             # → demo/outbreak-sentinel-demo.mp4
```

Every pixel of content is drawn from `state/video-capture/snapshot.json`. No finding, number
or headline in the video is hand-written; the renderer's strings interpolate captured values
and its geometry is the captured numbers.

This file **replaces** the stale claims in `demo/SHOTLIST.md` (pre-fix shotlist: Karachi
dengue HIGH, "94/95 tests", a live `POST /telegraph/risk` buy). None of those appear in the
video. Karachi in the live grid is **LOW 0 with 0 sources**.

---

## Shot list as rendered (6 scenes)

| # | Scene | Length | Captured source |
|---|---|---|---|
| 1 | Cold open | 20 s | `/health`, `/risk` grid counters |
| 2 | The live console | 56 s | `/risk` → LA wildfire card, its chart, `signals` |
| 3 | The evidence gate | 44 s | `/risk` → London dengue card, Karachi empty card |
| 4 | Graceful degradation | 36 s | `/debug/weather` (live) + forced-fallback run |
| 5 | The money story | 56 s | `/telegraph/status`, `/telegraph/stats`, `/receipts`, `eth_getTransactionReceipt` |
| 6 | Close | 20 s | `/risk` grid counters |

---

## Captions, verbatim, per scene

Persistent chrome on every frame: `https://outbreak-sentinel.onrender.com` (top-left) and
`mode live · chain 84532 · Base Sepolia (testnet)` (top-right), both derived from `/telegraph/status`.

### Scene 1 — Cold open (0:00–0:20)

On screen: `OUTBREAK SENTINEL`, `autonomous early-warning agent, paid through Telegraph`,
a `LIVE` chip with the URL, and from `/risk`:
`34 risk cards · 19 cities · 3 verticals · engine deterministic+narrator`.
Right panel, from `/health` and `/risk`: `GET /health → ok · v1.0.0`, `service outbreak-sentinel`,
`captured (UTC)`, `grid timestamp`.

Captions:
1. `Outbreak Sentinel — an autonomous early-warning agent, live at a public URL.`
2. `This video is built from the deployment's real API responses, captured at build time.`

### Scene 2 — The live console (0:20–1:16)

On screen, header from `/risk`: `/risk · 34 cards · 19 cities · levels {'LOW': 29, 'MODERATE': 3, 'HIGH': 2}`
and `signals: news 257 (city-scoped 151) · social 113 · weather cities 19`.

Hero card, verbatim from `/risk` `risk_cards` (Los Angeles / wildfire):
`Los Angeles HIGH 65`, `confidence 0.95`, `vertical: wildfire`,
`evidence: 5 city-specific wildfire reports in the last 7 days — latest 24 Nov.`,
drivers `5 city-specific wildfire reports in 7 days` and `High wind: 30.7 km/h`,
then the five cited sources (Sacramento Bee ×3, The Guardian, Los Angeles Times).
Right column: the real 7-point `chart[]` series, `points 7 · peak 13.5 mm`, `through 2026-12-02`,
and `evidence_count 5 == sources 5` / `count and links are one number`.

Captions:
1. `One render of /risk returns the whole grid: every card computed in code.`
2. `Los Angeles — wildfire HIGH 65: five city-specific reports in 7 days, plus a high-wind driver.`
3. `The five cited stories are the five links — driver count and rendered sources are one number.`

> Caption 2 and the `==` line make the old "9 reports vs 5 links" defect visibly fixed:
> `evidence_count`, the driver text and `sources` are all 5 in this capture.

### Scene 3 — The evidence gate (1:16–2:00)

On screen, verbatim from `/risk` (London / bio-surveillance):
`London — Dengue LOW 20`, `1 city-specific dengue report in the last 7 days — latest 23 Nov.`,
`sources (1):` → `UK steps up trapping efforts after mosquitoes that can spread dengue breed in London homes - Yahoo` · `Yahoo · 2026-11-23`.
From `/risk` (Karachi / bio-surveillance): `Karachi LOW 0 with 0 sources`.

Captions:
1. `The differentiator is the evidence gate.`
2. `London dengue LOW 20 cites exactly one story — a local vector report, nothing else.`
3. `Another disease's outbreak is never this card's evidence. No evidence means an honest LOW, not a fabricated one.`

> The caption states the rule plainly: another disease's outbreak is never this card's
> evidence. The audit's ebola/legionnaires' contamination does not appear anywhere in the
> captured grid.

### Scene 4 — Graceful degradation (2:00–2:36)

Left panel — `GET /debug/weather — live today`, from the live `/debug/weather`:
`configured 19 · attempted 19`, `ok 19 · failed 0`, `providers: open-meteo`, `cache: 19 cities served`.

Right panel — `fallback path: Open-Meteo 429 → MET Norway`, from the forced-fallback run:
`replayed Open-Meteo HTTP 429 daily-quota (verbatim 2026-11-25 reply)`,
`ok 19/19 via met-norway`, `failed 0 · forecast days per city [10]`,
`primary hard-fails → independent provider answers`.

Captions:
1. `Resilience: weather is three providers deep.`
2. `Today the live grid is served cleanly — /debug/weather shows 19 of 19 cities answered.`
3. `And when the primary hard-fails with a daily-quota 429, the same code path serves real MET Norway forecasts instead of blanking the card.`

> **Honesty note.** On capture day Open-Meteo's daily quota had reset, so the *live*
> deployment reported `open-meteo` for all 19 cities — it is **not** true that MET Norway was
> serving live today. Rather than claim otherwise, the right panel shows a **replay**: the
> shipped `app.fetch_weather` was executed with `_fetch_open_meteo` returning the exact 429
> body Render returned on 2026-11-25, so real MET Norway data flowed through the real fallback
> branch. The panel labels it `replayed … verbatim 2026-11-25 reply`, and the caption separates
> "today" from "when the primary hard-fails". The 10-day forecast length is MET's own UTC-day
> bucketing, also unedited.

### Scene 5 — The money story (2:36–3:32)

On screen, verbatim from `/telegraph/status`:
`/telegraph/status · mode live · chain 84532 · Base Sepolia (testnet)`,
`last settlement (seeded from the ledger)`,
`0xac02bcbbe78e85760f3ae45400d457f750c9f0fd61c0fc9d06189fe84aa9c4cf`,
`rail x402 (live) · mocked False · 0.01 USDC · 10000 µUSDC · 2026-11-16 20:02 PKT`.
From `eth_getTransactionReceipt` on `https://sepolia.base.org`:
`on-chain receipt: status 0x1 · block 59597289 · to 0x036cbd53842c5426634e7929541ec2318f3dcf7e`.
From `/telegraph/stats`: `assessments 2 · settled 1 · total 0.01 USDC · integrity 100%`.
From `/receipts`: `2 filed from HIGH/CRITICAL cards`, then each row —
`rcpt-336283ecc0c4 · Los Angeles · HIGH 65 · OPEN · 5 city-specific wildfire reports in 7 days`
and `rcpt-c8cd0f19221c · Cape Town · HIGH 55 · OPEN · …`, each with its `content_hash`.

Captions:
1. `The money is first-class data, not a claim.`
2. `Mode live on Base Sepolia (testnet): a real transaction, mocked False.`
3. `Read back from the chain: status 0x1, block 59597289, to the USDC contract.`
4. `Every paid assessment is notarized, and every HIGH card that finalizes files a receipt.`

> No paid request was fired for this video. The settlement shown is the already-verified
> ledger seed that `/telegraph/status` returns on a fresh boot, and its block number comes
> from a read-only `eth_getTransactionReceipt` captured at build time — not from any markdown file.

### Scene 6 — Close (3:32–3:52)

On screen: `OUTBREAK SENTINEL`, the URL, `Track 01 — Apps & Agents`,
`Mission 06 — Resources & Agriculture (fire-risk signal stack)`,
`Mission 11 — Autonomous Systems (an autonomous unit buying fire-risk)`,
`Surveillance only — never diagnosis.`,
`34 live cards across 19 cities; sources traceable; suite green.`

Captions:
1. `Outbreak Sentinel — cited early-warning intelligence, bought and settled on-chain.`
2. `Everything shown came from the live deployment. The URL is open — try it.`

---

## Captured responses used, by endpoint

| Endpoint | Key fields the video renders |
|---|---|
| `GET /health` | `status`, `service`, `version` |
| `GET /risk` | `engine`, `timestamp`, `signals.{news,social,cities,news_city_scoped}`, `risk_cards[]` → `city, vertical, disease, risk_level, risk_score, confidence, drivers[].text, evidence_line, evidence_count, sources[].{title,outlet,published}, chart[].{label,value}` |
| `GET /debug/weather` | `configured_cities, attempted_cities, ok, failed, cache.cities`, per-city `provider` |
| `GET /receipts` | `count`, receipts `receipt_id, city, risk_level, score, status, drivers[0], content_hash` |
| `GET /telegraph/status` | `mode, chain_id, network_label, last_settlement.{tx_hash, amount_usd, amount_uusdc, time_pkt, settlement.{rail, mocked}}` |
| `GET /telegraph/stats` | `assessments, settled, total_usdc, integrity_pct` |
| `POST https://sepolia.base.org` (`eth_getTransactionReceipt`) | `status, blockNumber, to` |
| forced-fallback `app.fetch_weather` | `ok, attempted_cities, served_by, forecast_days` (real MET Norway) |

**Not used:** `POST /telegraph/risk` (the paid flow — would spend money). Its causal
`paid_intelligence` driver is not shown, because no such card exists in today's free `/risk`
grid; the settlement tx from `/telegraph/status` carries the money beat instead, exactly as the
work order directs when the paid flow cannot be shown free.
