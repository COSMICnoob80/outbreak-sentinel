# VIDEO-CAPTIONS — Outbreak Sentinel demo (Soldier V-5, cut v3)

**Deliverable:** `demo/outbreak-sentinel-demo-v3.mp4` — 1920×1080, 30 fps, H.264, **232 s**,
captioned, **no audio track**. Built from real captured API responses, not screen capture.

**Kept verbatim in the repo, never rebuilt:**
- `demo/outbreak-sentinel-demo-v1-backup.mp4` — the approved-flow v1 cut (the motion reference).
- `demo/outbreak-sentinel-demo.mp4` — the v2 cut (the skin and neutral-caption reference).

**Rebuild:**
```bash
env -u PYTHONPATH .venv/bin/python demo/render_video.py             # → demo/outbreak-sentinel-demo-v3.mp4
env -u PYTHONPATH .venv/bin/python demo/render_video.py --stills demo/screenshots   # → 6 form PNGs
env -u PYTHONPATH .venv/bin/python demo/render_video.py --montage demo/frames/montage-v5.png
```
No re-capture was performed. Every render reads the same `state/video-capture/snapshot.json`
that v1 and v2 were cut from.

---

## What v3 is: v1's motion, v2's skin

The operator watched both cuts and ruled: **v1's animations, transitions, flow, size and
magnification were better; v2's console-mirrored visuals and Inter were better.** The
instruction was to re-skin v1, not rebuild it. v2 rebuilt the renderer instead and the motion
drifted. v3 takes v1's motion engine and renders v2's console scenes through it.

### Motion carried over from v1
- **Reveal pacing.** `REVEAL_SPAN = 0.55` (v2 had stretched it to 0.58). Each scene finishes
  revealing its items at 55% of its runtime, then holds a complete frame so the later captions
  land on finished content.
- **One uninterrupted reveal per scene.** v1 never cuts inside a scene. v2 added a second
  mid-scene cut in scene 2 (cut to a 1.6× cited-sources plate, ramp, then hold). That cut is
  gone: all five cited reports now render inline on the LA card, so scene 2 is a single reveal
  like every v1 scene. The point the V-4 plate was making — the card's source count and the
  rendered list are the same number — is now read off the card itself.
- **One magnification move, v1's numbers.** Scene 5 ends on the evidence hold:
  `ZOOM_RAMP_S = 0.5`, `ZOOM_HOLD_S = 4.0`, `ZOOM_MAX = 1.5`. The plate is laid out once at
  1.5× and the push-in eases from the whole-block fit (1/1.5) up to 1:1, so the widest framing
  *is* the layout and nothing can leave the frame at any instant.
- **Content-sized panels.** v1 sized a card to what it said; v2 stretched panels to fixed
  heights, which produced dead bands (the worst was ~190 px under the London card). v3 measures
  each panel with a `Measure` pass and paints it to its own content.
- **Magnification, restored.** v2 rendered the console as a whole page (instrument strip, three
  stacked cards, right rail) at page scale. v3 renders v1's composition — one large hero card
  with its cited reports and the chart beside them — in Inter, so type is back at the size the
  operator preferred.

### Skin carried over from v2
`dashboard/index.html` `:root`, with the OKLCH tokens converted to sRGB at the same L/C/h
values: ground `#0a0d0a`, surfaces `#121612/#191e19/#222822`, hairlines `#2b302b/#404840`,
ink ladder `#f2f6f2…#cfd5cf`, one lime accent `#ade84f` for live/verified state only, and the
severity ramp red 22° → orange 44° → amber 92° → neutral 146°
(`#ff9a99 / #ffa976 / #f4d269 / #b6c1b6`). Masthead with brand mark and `live` badge, severity
left edges on cards, tag/cite chips, `.rail-row` telemetry, the 7-day spark from `chart[]`.

**Inter** (SIL OFL 1.1), vendored at `demo/assets/fonts/InterVariable.ttf` with its licence at
`demo/assets/fonts/OFL.txt`; weight and optical-size axes are driven per size. Inter has no
monospace companion, so telemetry (hashes, ids, counts) uses DejaVu Sans Mono — the role the
console's `--font-mono` stack plays. No hotlinking, no CDN.

### Voice (unchanged from v2)
Every caption that addressed or name-dropped a judge is gone; narration states what the system
does and shows. The honest-capture line is kept verbatim.

### Captions: one size step larger
Also per operator feedback (projector and phone legibility): the bottom strip went from
**Inter 26 px → Inter 30 px**, line advance **38 → 42 px**, wrap width `SHELL_W - 120` →
`SHELL_W - 60`. Every caption was re-checked at the new size: all 18 fit on one line except
scene 4's third, which wraps to two — none exceed the two-line clamp, and the strip stays
inside `MARGIN_X`.

### Music: none
No audio stream at all. The operator is licensing a track separately and muxes it after this
build; nothing here assumes a track, so muxing needs no re-render.

---

## Caption diff, V-4 → V-5

| Scene | V-4 caption (gone) | V-5 caption (shipped) |
|---|---|---|
| 1 | `Outbreak Sentinel — an autonomous early-warning console, running at a public URL.` | `Outbreak Sentinel — an autonomous early-warning agent, live at a public URL.` |
| 2 (3rd) | `The card counts 5 sources; the news driver counts 5 reports. Same number.` | `The card counts 5 sources — every one of them cited below it. Same number.` |
| 2 (4th) | `Each of those stories, one row per cited report — so the count on the card and the rendered sources are visibly one list.` | `Count the cited reports on the card: the driver's report count and the rendered sources are one list, not two claims.` |
| 4 (on screen) | `Primary hard-fails with a daily-quota 429 — the same code path serves real forecasts from an independent provider.` | kept verbatim |
| 5 (5th) | `Full transaction hash and both receipts — fitted to the frame, never cropped.` | kept verbatim |

Kept verbatim: `This video is built from the deployment's real API responses, captured at
build time.` — the honest-capture disclaimer stays.

**Two literals removed from the renderer.** V-4 drew `19 / 19 ok` (scene 4) and `HIGH 2`
(scene 5 ledger strip) as hardcoded strings. Both now interpolate the capture
(`debug_weather.ok`/`attempted_cities`, `telegraph_stats.verdicts`). No rendered string in v3
is hand-written.

---

## Shot list as rendered (6 scenes, 232 s)

| # | Scene | Length | Captured source |
|---|---|---|---|
| 1 | Cold open | 20 s | `/risk` grid counters, `/health` |
| 2 | The live console | 56 s | `/risk` → LA wildfire card, its chart, `signals`, `levels` |
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
a lime progress rule. The bottom caption strip is Inter 30 px on a hairline-ruled bar.

### Scene 1 — Cold open (0:00–0:20)

On screen: `Outbreak Sentinel` at title scale, `autonomous early-warning agent, paid through
Telegraph`, the live URL pill, the grid line
`34 risk cards · 19 cities · 3 verticals · engine deterministic+narrator`, the amber
`SURVEILLANCE ONLY — never diagnosis, never treatment advice`, and a `GET /health` panel
(`status ok · v1.0.0`, `service outbreak-sentinel`, `captured (UTC)`, `grid timestamp`).

Captions:
1. `Outbreak Sentinel — an autonomous early-warning agent, live at a public URL.`
2. `This video is built from the deployment's real API responses, captured at build time.`

### Scene 2 — The live console (0:20–1:16)

One uninterrupted reveal. On screen: the LA wildfire card at v1's scale — `Los Angeles`,
`HIGH` chip, `65 /100`, `wildfire`, `receipt rcpt-336283ecc0c4`, `5 sources`,
`5 city-specific wildfire reports in the last 7 days — latest 24 Nov.`, both drivers
(`5 city-specific wildfire reports in 7 days`, `High wind: 30.7 km/h`), then
`sources (5) — verbatim from /risk` with **all five cited reports** as numbered rows, each with
its outlet and date. Beside them: `confidence 0.95`, the captured 7-point
`7-day precipitation outlook` spark, `points 7 · peak 13.5 mm`, `through 2026-12-02`, and
`evidence_count 5 == sources 5` / `count and links are one number`.

Captions:
1. `One render of /risk returns the whole grid: 34 cards, every one computed in code.`
2. `Los Angeles — wildfire HIGH 65: 5 city-specific reports in seven days, plus a high-wind driver.`
3. `The card counts 5 sources — every one of them cited below it. Same number.`
4. `Count the cited reports on the card: the driver's report count and the rendered sources are one list, not two claims.`

> The four captions escalate to the count-parity claim while the five rows are already on
> screen — the claim is read off the frame, not asserted over a cut.

### Scene 3 — The evidence gate (1:16–2:00)

On screen, verbatim from `/risk` (London / bio-surveillance): `London`, `Dengue`, `LOW 20`,
`Dengue · 1 source · confidence 60%`, `1 city-specific dengue report in the last 7 days —
latest 23 Nov.`, `CONTRIBUTING SIGNALS (1)` with its bar, the `AI` narrative and `ACTION`
line, `CITED SOURCES (1)` with the single `UK steps up trapping efforts… · Yahoo · 2026-11-23`
row, and the receipt block (`receipt`, `rcpt-…`, `status OPEN`, `content_hash`). Beside it, the
Karachi card from `/risk`: `LOW 0`, `0 — none for this city`, `no fabricated citation`, and a
`WHY THIS MATTERS` footer inside the same card. Under the London card, v1's two payoff lines:
`The one cited story is a local vector report — not another disease's outbreak.` and
`No city-specific evidence stays honest: e.g. Karachi LOW 0 with 0 sources.`

Captions:
1. `The differentiator is the evidence gate.`
2. `London dengue LOW 20 cites exactly one story — a local vector report, nothing else.`
3. `Another disease's outbreak is never this card's evidence. No evidence means an honest low, not a fabricated one.`

### Scene 4 — Graceful degradation (2:00–2:36)

Left panel — `GET /debug/weather — live today`, from the live `/debug/weather`:
`configured cities 19`, `attempted cities 19`, `ok 19`, `failed 0`, `provider open-meteo`,
`cache 19 cities served (…s old)`, plus the generation stamp, with a `19 / 19 ok` chip
interpolated from the capture.

Right panel — `FALLBACK PATH — PRIMARY 429`, from the forced-fallback run:
`replayed condition Open-Meteo HTTP 429 daily-quota (verbatim 2026-11-25 reply)`,
`cities attempted 19`, `served ok 19/19`, `failed 0`, `served by met-norway`,
`forecast days / city 10`, and the note
`Primary hard-fails with a daily-quota 429 — the same code path serves real forecasts from an
independent provider.`

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
> "today" from "when the primary returns a 429". The 10-day forecast length is MET's own
> UTC-day bucketing, also unedited.

### Scene 5 — The money story (2:36–3:32)

On screen: an `ON-CHAIN SETTLEMENT` panel with an accent top edge and a
`live settlement proven` chip, showing the last settlement (`tx hash`,
`rail x402 (live) · mocked False · 0.01 USDC · 10000 µUSDC · 2026-11-16 20:02 PKT`) and the
on-chain receipt rail rows (`status 0x1`, `block 59597289`, `to (USDC) 0x036cbd…cf7e`,
`from 0x97d38a…f6a5`, `logs 2`, `rpc https://sepolia.base.org`); a `RECEIPTS` panel with both
receipt cards, each severity-edged with `score/100`, level chip, driver and `content_hash`; and
a content-sized ledger strip (`assessments 2`, `settled 1`, `total 0.01 USDC`,
`integrity 100%`, `verdicts HIGH 2` — interpolated from `telegraph_stats.verdicts`,
`ledger sha256, append-only`).

At **207.5 s** (92% through the scene) the camera cuts to the settlement detail view — header
`settlement detail — full ledger record` — and pushes in, then holds:

- **207.5–208.0 s** — the whole panel is fitted: the settlement panel, both receipt rows and
  both content hashes are drawn at 1.5× type but shown scaled to 1/1.5, so the entire block is
  visible and centred. Nothing is outside the frame.
- **208.0–212.0 s** — hold at 1:1, i.e. the literal 1.5× layout, for 4.0 s, ending at the scene
  cut. The tx hash (`0xac02bb…c4cf`) and both receipt rows are fully legible.
- Laid out inside `ZOOM_BOX = (120, 162, 1800, 916)`; the renderer raises rather than drawing
  if the text does not fit, so a longer hash in a future snapshot fails the build instead of
  clipping.

Captions:
1. `The money is first-class data, not a claim.`
2. `Mode live on Base Sepolia (testnet): a real transaction, mocked False.`
3. `Read back from the chain: status 0x1, block 59597289, to the USDC contract.`
4. `Every paid assessment is notarized, and every HIGH card that finalizes files a receipt.`
5. `Full transaction hash and both receipts — fitted to the frame, never cropped.`

> No paid request was fired for this video. The settlement shown is the already-verified
> ledger seed that `/telegraph/status` returns on a fresh boot, and its block number comes
> from a read-only `eth_getTransactionReceipt` captured at build time.

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
| `GET /risk` | `engine`, `timestamp`, `signals.*`, `levels`, `verticals`, `risk_cards[]` → `city, vertical, disease, risk_level, risk_score, confidence, drivers[].{kind,text}, evidence_line, evidence_count, sources[].{title,outlet,published}, chart[].{label,value}` |
| `GET /debug/weather` | `configured_cities, attempted_cities, ok, failed, cache.{cities,age_s}, generated_at`, per-city `provider` |
| `GET /receipts` | `count`, receipts `receipt_id, city, risk_level, score, status, drivers[0], content_hash` |
| `GET /telegraph/status` | `mode, chain_id, network_label, last_settlement.*` |
| `GET /telegraph/stats` | `assessments, settled, total_usdc, integrity_pct, verdicts` |
| `POST https://sepolia.base.org` (`eth_getTransactionReceipt`) | `status, blockNumber, to, from, logCount` |
| forced-fallback `app.fetch_weather` | `ok, attempted_cities, served_by, forecast_days` (real MET Norway) |

**Not used:** `POST /telegraph/risk` (the paid flow — would spend money). Its causal
`paid_intelligence` driver is not shown, because no such card exists in today's free `/risk`
grid; the settlement tx from `/telegraph/status` carries the money beat instead.
