# VIDEO-CAPTIONS — Outbreak Sentinel demo (Soldier V-3)

**Deliverable:** `demo/outbreak-sentinel-demo.mp4` — 1920×1080, 30 fps, H.264, **232 s** (3:52),
captioned, **no audio track**. Built from real captured API responses, not screen capture.

**Forked predecessor:** `demo/outbreak-sentinel-demo-v1-backup.mp4` — the approved-flow v1
(video V-2), kept verbatim in the repo (sha256 `11d1566d…34e5`).

**Rebuild:**
```bash
./demo/capture_video_data.sh                                        # live GETs → state/video-capture/*.json
env -u PYTHONPATH .venv/bin/python demo/capture_video_data.py       # → snapshot.json (+ forced MET fallback, on-chain read)
env -u PYTHONPATH .venv/bin/python demo/render_video.py             # → demo/outbreak-sentinel-demo.mp4
env -u PYTHONPATH .venv/bin/python demo/render_video.py --stills demo/screenshots   # → 6 form PNGs
```

V-3 keeps V-2's scene flow, durations and reveal animations and changes how every frame
**looks**, plus the voice of the narration:

1. **Console-mirrored design system.** The palette is no longer an invented terminal
   scheme — it is `dashboard/index.html`'s `:root`, with the OKLCH tokens converted to sRGB at
   the same L/C/h values: ground `#0a0d0a`, surfaces `#121612/#191e19/#222822`, hairlines
   `#2b302b/#404840`, ink ladder `#f2f6f2…#cfd5cf`, one lime accent `#ade84f` for live/verified
   state only, and the severity ramp red 22° → orange 44° → amber 92° → neutral 146°
   (`#ff9a99 / #ffa976 / #f4d269 / #b6c1b6`). Scenes reuse the console's own anatomy: the
   masthead with brand mark and `live` badge, the five-cell instrument strip, the
   `Top open signal` hero with a severity top edge, risk cards with a 3px severity left edge
   and a right-aligned `score/100` + `.level` wash chip, tag/cite chips, `.rail-row` telemetry,
   and the 7-day spark drawn from `chart[]`.
2. **Inter.** Type is Inter Variable (SIL OFL 1.1), vendored at `demo/assets/fonts/InterVariable.ttf`
   with its license at `demo/assets/fonts/OFL.txt`; the weight and optical-size axes are driven
   per size. Inter has no monospace companion, so telemetry (hashes, ids, counts) uses DejaVu
   Sans Mono — the role the console's `--font-mono` stack plays. No hotlinking, no CDN.
3. **Neutral voice.** Every caption that addressed or name-dropped judges is gone; narration
   now states what the system does and shows. The honest-capture line is kept.
4. **No music.** The cut is caption-driven with no audio stream, on purpose: a public
   hackathon submission must not carry a licensed track.

Every pixel of content is drawn from `state/video-capture/snapshot.json`. No finding, number
or headline in the video is hand-written; the renderer's strings interpolate captured values
and its geometry is the captured numbers.

This file **replaces** the stale claims in `demo/SHOTLIST.md` (pre-fix shotlist: Karachi
dengue HIGH, "94/95 tests", a live `POST /telegraph/risk` buy). None of those appear in the
video. Karachi in the live grid is **LOW 0 with 0 sources**.

---

## Caption diff, V-2 → V-3

The only narration removed was the judge framing; no factual claim was dropped.

| Scene | V-2 caption (gone) | V-3 caption (shipped) |
|---|---|---|
| 1 | `Outbreak Sentinel — an autonomous early-warning agent, live at a public URL.` | `Outbreak Sentinel — an autonomous early-warning console, running at a public URL.` |
| 2 | `One render of /risk returns the whole grid: every card computed in code.` | `One render of /risk returns the whole grid: 34 cards, every one computed in code.` |
| 4 (on screen) | `A judge sees degradation, not a dead panel: weather can fail without erasing a card.` | `Primary hard-fails with a daily-quota 429 — the same code path serves real forecasts from an independent provider.` |
| 4 (caption 3) | `And when the primary hard-fails with a daily-quota 429, …` | `When the primary returns a daily-quota 429, …` |
| 5 (caption 5) | `Read it yourself — full tx hash and both receipts, …` | `Full transaction hash and both receipts — fitted to the frame, never cropped.` |

Kept verbatim: `This video is built from the deployment's real API responses, captured at
build time.` — the honest-capture disclaimer stays.

---

## Shot list as rendered (6 scenes)

| # | Scene | Length | Captured source |
|---|---|---|---|
| 1 | Cold open | 20 s | `/risk` grid counters, `/telegraph/stats`, `/receipts` |
| 2 | The live console | 56 s | `/risk` → LA wildfire card, its chart, `signals`, `levels`, `verticals` |
| 3 | The evidence gate | 44 s | `/risk` → London dengue card, Karachi empty card |
| 4 | Graceful degradation | 36 s | `/debug/weather` (live) + forced-fallback run |
| 5 | The money story | 56 s | `/telegraph/status`, `/telegraph/stats`, `/receipts`, `eth_getTransactionReceipt` |
| 6 | Close | 20 s | `/risk` grid counters, `/telegraph/stats` |

---

## Captions, verbatim, per scene

Persistent chrome on every frame, mirroring the console masthead: a lime brand mark,
`Outbreak Sentinel`, a `live` status badge, `mode live · chain 84532 · Base Sepolia (testnet)`
and `captured 2026-11-26T08:08:50+00:00` (top-right, from `/telegraph/status` and the capture
stamp), the console subtitle line, a scene counter bottom-left, the live URL bottom-right, and
a lime progress rule.

### Scene 1 — Cold open (0:00–0:20)

On screen: the instrument strip — `News signals 257` (city-scoped 151), `Risk cards 34`
(19 cities), `Fusion engine deterministic+narrator`, `Settlements 1` (of 2 assessments),
`Receipt integrity 100%`; the `TOP OPEN SIGNAL` hero for `Los Angeles · wildfire` with a HIGH
severity top edge, `HIGH 65/100 · confidence 95% · 2 drivers · 5 sources`, its summary and
evidence line, and `highest of 34 cards in this window`; a `SYSTEM STATUS` rail
(Settlements/Receipts/Feed/Coverage/Engine); and the first three risk cards as flat rows.

Captions:
1. `Outbreak Sentinel — an autonomous early-warning console, running at a public URL.`
2. `This video is built from the deployment's real API responses, captured at build time.`

### Scene 2 — The live console (0:20–1:16)

On screen: the instrument strip, then a `RISK CARDS` panel whose lead card is verbatim from
`/risk` (Los Angeles / wildfire) — `Los Angeles`, `wildfire`, `receipt rcpt-336283ecc0c4`,
`5 sources`, `RISK SCORE 65/100`, `HIGH`, `evidence: 5 city-specific wildfire reports in the
last 7 days — latest 24 Nov.`, cite chips (Sacramento Bee ×3, The Guardian, Los Angeles Times),
the real 7-point `chart[]` spark with `min/max/▲` and `5 evidence == 5 sources`. Two compact
cards follow (Cape Town, London). The right `.rail` column shows `news signals 257`,
`city-scoped 151`, `wildfire-scoped 76`, `social 113`, `cities 19`, the severity bars
(HIGH 2 / MODERATE 3 / LOW 29), verticals, engine and grid timestamp.

Captions:
1. `One render of /risk returns the whole grid: 34 cards, every one computed in code.`
2. `Los Angeles — wildfire HIGH 65: five city-specific reports in seven days, plus a high-wind driver.`
3. `The five cited stories are the five links — driver count and rendered sources are one number.`

> Caption 2 and the `==` line make the old "9 reports vs 5 links" defect visibly fixed:
> `evidence_count`, the driver text and `sources` are all 5 in this capture.

### Scene 3 — The evidence gate (1:16–2:00)

On screen, verbatim from `/risk` (London / bio-surveillance): `London`, `Dengue`, `LOW 20`,
`1 city-specific dengue report in the last 7 days — latest 23 Nov.`, `CONTRIBUTING SIGNALS (1)`
with its bar, the `AI` narrative and `ACTION` line, and the single `Yahoo · 11-23` cite chip.
(London carries no receipt — receipts exist only for the two HIGH cards, Los Angeles and Cape
Town.) Beside it, the Karachi card from `/risk`: `LOW 0`, `0 — none for this city`,
`no fabricated citation`, and a `WHY THIS MATTERS` note.

Captions:
1. `The differentiator is the evidence gate.`
2. `London dengue LOW 20 cites exactly one story — a local vector report, nothing else.`
3. `Another disease's outbreak is never this card's evidence. No evidence means an honest low, not a fabricated one.`

> The caption states the rule plainly: another disease's outbreak is never this card's
> evidence. The audit's ebola/legionnaires' contamination does not appear anywhere in the
> captured grid.

### Scene 4 — Graceful degradation (2:00–2:36)

Left panel — `GET /debug/weather — live today`, from the live `/debug/weather`:
`configured cities 19`, `attempted cities 19`, `ok 19`, `failed 0`, `provider open-meteo`,
`cache 19 cities served`, plus the generation stamp.

Right panel — `FALLBACK PATH — PRIMARY 429`, from the forced-fallback run:
`replayed condition Open-Meteo HTTP 429 daily-quota (verbatim 2026-11-25 reply)`,
`cities attempted 19`, `served ok 19/19`, `failed 0`, `served by met-norway`,
`forecast days / city 10`.

Captions:
1. `Resilience: weather is three providers deep.`
2. `Today the live grid is served cleanly — /debug/weather shows 19 of 19 cities answered.`
3. `When the primary returns a daily-quota 429, the same code path serves real MET Norway forecasts instead of blanking the card.`

> **Honesty note.** On capture day Open-Meteo's daily quota had reset, so the *live*
> deployment reported `open-meteo` for all 19 cities — it is **not** true that MET Norway was
> serving live today. Rather than claim otherwise, the right panel shows a **replay**: the
> shipped `app.fetch_weather` was executed with `_fetch_open_meteo` returning the exact 429
> body Render returned on 2026-11-25, so real MET Norway data flowed through the real fallback
> branch. The panel labels it `replayed … verbatim 2026-11-25 reply`, and the caption separates
> "today" from "when the primary returns a 429". The 10-day forecast length is MET's own UTC-day
> bucketing, also unedited.

### Scene 5 — The money story (2:36–3:32)

On screen: an `ON-CHAIN SETTLEMENT` panel with an accent top edge and a
`live settlement proven` chip, showing the last settlement (`tx hash`,
`rail x402 (live) · mocked False · 0.01 USDC · 10000 µUSDC · 2026-11-16 20:02 PKT`) and the
on-chain receipt rail rows (`status 0x1`, `block 59597289`, `to (USDC) 0x036cbd…cf7e`,
`from 0x97d38a…f6a5`, `logs 2`, `rpc https://sepolia.base.org`); a `RECEIPTS` panel with both
receipt rows, each as a severity-edged card with `score/100`, level chip, driver and
`content_hash`; and a ledger strip (`assessments 2`, `settled 1`, `total 0.01 USDC`,
`integrity 100%`, `verdicts HIGH 2`, `ledger sha256, append-only`).

At **207.5 s** (92% through the scene) the camera cuts to the evidence detail view and pushes
in, then holds:

- **207.5–208.0 s** — the whole panel is fitted: the settlement panel, both receipt rows and
  both content hashes are drawn at 1.5× type but shown scaled to 1/1.5 so the entire block is
  visible and centered. Nothing is outside the frame.
- **208.0–212.0 s** — hold at 1:1, i.e. the literal 1.5× layout, for 4.0 s, ending at the scene
  cut. The tx hash (`0xac02bb…c4cf`) and both receipt rows are fully legible.
- The block is laid out inside `ZOOM_BOX = (120, 162, 1800, 916)`; the renderer raises rather
  than drawing if the text does not fit, so a longer hash in a future snapshot fails the build
  instead of clipping. Whitespace, not type size, absorbs any shortfall.

Captions:
1. `The money is first-class data, not a claim.`
2. `Mode live on Base Sepolia (testnet): a real transaction, mocked False.`
3. `Read back from the chain: status 0x1, block 59597289, to the USDC contract.`
4. `Every paid assessment is notarized, and every HIGH card that finalizes files a receipt.`
5. `Full transaction hash and both receipts — fitted to the frame, never cropped.`

> No paid request was fired for this video. The settlement shown is the already-verified
> ledger seed that `/telegraph/status` returns on a fresh boot, and its block number comes
> from a read-only `eth_getTransactionReceipt` captured at build time — not from any markdown file.

### Scene 6 — Close (3:32–3:52)

On screen: `Outbreak Sentinel`, the URL in lime, `Track 01 — Apps & Agents`,
`Mission 06 — Resources & Agriculture (fire-risk signal stack)`,
`Mission 11 — Autonomous Systems (an autonomous unit buying fire-risk)`,
`Surveillance only — never diagnosis, never treatment advice.`,
`34 live cards across 19 cities; every claim traceable to a source; receipt ledger append-only.`,
and the instrument strip once more.

Captions:
1. `Outbreak Sentinel — cited early-warning intelligence, bought and settled on-chain.`
2. `Everything shown came from the live deployment. The URL is open — try it.`

---

## Captured responses used, by endpoint

| Endpoint | Key fields the video renders |
|---|---|
| `GET /health` | `status`, `service`, `version` |
| `GET /risk` | `engine`, `timestamp`, `signals.{news,social,cities,news_city_scoped,wildfire_city_scoped}`, `levels`, `verticals`, `risk_cards[]` → `city, vertical, disease, risk_level, risk_score, confidence, drivers[].{kind,text}, evidence_line, evidence_count, sources[].{title,outlet,published}, chart[].{label,value}` |
| `GET /debug/weather` | `configured_cities, attempted_cities, ok, failed, cache.{cities,age_s}, generated_at`, per-city `provider` |
| `GET /receipts` | `count`, receipts `receipt_id, city, risk_level, score, status, drivers[0], content_hash` |
| `GET /telegraph/status` | `mode, chain_id, network_label, last_settlement.{tx_hash, amount_usd, amount_uusdc, time_pkt, settlement.{rail, mocked}}` |
| `GET /telegraph/stats` | `assessments, settled, total_usdc, integrity_pct` |
| `POST https://sepolia.base.org` (`eth_getTransactionReceipt`) | `status, blockNumber, to, from, logCount` |
| forced-fallback `app.fetch_weather` | `ok, attempted_cities, served_by, forecast_days` (real MET Norway) |

**Not used:** `POST /telegraph/risk` (the paid flow — would spend money). Its causal
`paid_intelligence` driver is not shown, because no such card exists in today's free `/risk`
grid; the settlement tx from `/telegraph/status` carries the money beat instead, exactly as the
work order directs when the paid flow cannot be shown free.
