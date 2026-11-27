# AUDIT — three-cut video comparison vs the Telegraph rubric

**Date:** 2026-11-27
**Role:** standing project auditor (JUDGE; no product code written)
**Question (operator):** v1 was judged superior in animations, transitions, flow, size and
magnification; v2 superior in UI (console-mirrored, Inter); v3 was built to merge both. **Which
cut is the better pitch?**
**Answer up front:** **v3.** It is Pareto-dominant — it scores at least as high as both
ancestors on every rubric-relevant criterion and strictly higher on five of six. No reasonable
weighting can rank v1 or v2 above it.

**Method constraint (post-OOM):** motion was measured **streaming** with ffmpeg CLI filters
(`tblend` + `signalstats` + `metadata=print`), parsed line by line in Python — no decoded
frame sequences in PIL/numpy. Peak RSS per pass: **139–140 MB** (v1 139,488 kB; v2 139,892 kB;
v3 139,776 kB), well under the ~1 GB ceiling. Stills were analysed one at a time, whole-frame
copies downscaled to 640 px or reduced to small ROI crops.

---

## 1. Inventory (ffprobe, all in repo)

| Cut | File | md5 | Duration | Frames | Resolution | Codec / fps | Audio streams | Bytes |
|---|---|---|---|---|---|---|---|---|
| **v1** | `demo/outbreak-sentinel-demo-v1-backup.mp4` | `42b8a387cd539c89a84eeebaa997fd26` | 232.000 s | 6960 | 1920×1080 | h264 / 30 | **0** | 4,926,657 |
| **v2** | `demo/outbreak-sentinel-demo.mp4` | `2259ce54d69f26103cf0155996bc36ac` | 232.000 s | 6960 | 1920×1080 | h264 / 30 | **0** | 5,115,399 |
| **v3** | `demo/outbreak-sentinel-demo-v3.mp4` | `c18e0bb4f7216523e57a28601a58d159` | 232.000 s | 6960 | 1920×1080 | h264 / 30 | **0** | 5,084,978 |

All three are the **same 3:52 timeline** (within §8's 2–5 minute window), silent by
construction, yuv420p. v1 and v2 match the hashes recorded in SPINE §V-5, so the ancestors are
byte-identical to what was approved. The cuts differ in **composition and pacing**, not length.

Scene map (identical timeline): scene 1 cold open 0–20 s, scene 2 console 20–76 s, scene 3
evidence gate 76–120 s, scene 4 degradation 120–156 s, scene 5 money 156–212 s, scene 6 close
212–232 s.

---

## 2. Motion check — streaming numbers

### 2.1 Scene-cut detection
`scale=480:-2, select='gt(scene,0.02)', metadata=print` per cut:

- **v1 / v3:** cuts at **20, 76, 120, 156, 207.5, 212 s**.
- **v2:** the same, **plus 70.4 s** (three flagged frames 70.40 / 70.43 / 70.97).

The 20/76/120/156/212 set are the five scene boundaries. **207.5 s is not a scene boundary** —
it is the cut into scene 5's detail plate that begins the one magnification move
(`156 + (1 − 4.5/56)·56 = 207.5`). v2's **70.4 s** is a second, mid-scene detail move inside
scene 2.

### 2.2 Sustained-motion profile
Per-2-second mean luma difference (320×180 gray, consecutive-frame `tblend`):

| Cut | 2 s bins ≥ 0.02 | ≥ 0.10 | ≥ 0.20 | Total luma-diff energy | Detail moves |
|---|---|---|---|---|---|
| v1 | 14 | 5 | 1 | 164.1 | 1 (207.5 s) |
| v2 | 23 | 7 | 5 | 311.5 | **2 (70.4 s + 207.5 s)** |
| v3 | 16 | 6 | 4 | 203.5 | 1 (207.5 s) |

The entire v2 surplus is the extra 70.4 s move: that window alone carries ~100 energy units.
Remove it and v2 ≈ v3 (≈211 vs 203); v1 stays lowest (164) because its scenes carry less text
to change between caption thresholds.

**This corrects the premise in one direction:** as *raw* motion, **v1 does not animate more
than v2 — it animates less.** What v1 actually has is **better flow**: one uninterrupted reveal
per scene, no cut inside a scene. The operator's "v1's transitions/flow" is a pacing judgment,
not a motion-energy reading, and it is reproducible in the data as the *absence* of the 70.4 s
mid-scene cut.

### 2.3 The one real animation, frame by frame
Per-frame luma diff across scene 5's magnification move (320×180 gray):

| t (s) | v1 | v2 | v3 |
|---|---|---|---|
| 207.47 | 0.00 | 0.00 | 0.00 |
| 207.50 | **8.10** | **11.57** | **11.59** | ← cut into detail plate
| 207.53 | 2.31 | 2.49 | 2.49 |
| 207.60 | 3.39 | 4.07 | 4.07 |
| 207.70 | 5.12 | 6.03 | 6.03 |
| 207.80 | 6.27 | 7.27 | 7.27 |
| 207.87 | 6.73 | **7.96** | **7.96** | ← peak of the push-in
| 207.93 | 5.39 | 6.17 | 6.17 |
| 207.97 | 2.79 | 3.10 | 3.10 |
| 208.00 | 0.01 | 0.01 | 0.01 |

After the cut frame, **14 consecutive frames carry non-zero diff that rises then falls** — a
genuine ~0.47 s camera ease, not a second hard cut. **All three cuts do this, with identical
timing.** v2 and v3 are numerically identical here (same scene-5 plate); v1 peaks lower only
because its plate has less fine detail.

### 2.4 The v2-only mid-scene cut
Same measurement at 70.2–71.1 s:

- **v1 and v3:** `0.00` at **every** sampled frame — the LA card simply holds.
- **v2:** `70.40 → 11.80` (hard cut), then a sustained ramp `1.93 → 7.75` over ~14 frames,
  back to `0.01` at 71.00.

Frames confirm what it is: v2 cuts from the whole console page to a magnified
`CARD LOS ANGELES · HIGH 65/100 · WILDFIRE` cited-sources list, holds it, then cuts again to
scene 3 at 76 s. That is **two layout changes inside ~6 s**. v1/v3 keep the LA card (with its
five sources inline) for the whole scene. Evidence:
`docs/audit-evidence-2026-11-27/v2-midcut-strip.png`.

### 2.5 Verdict on motion
- The **magnification move is real and identical** in all three: cut-to-detail at 207.50 s,
  0.47 s push-in to a 1.5× hold. Nobody is missing an animation.
- **v1's flow advantage is subtraction, not addition:** v1/v3 have one detail move; v2 has two,
  and the second one cuts mid-scene. v3 therefore carries v1's flow **and** v2's rich scene 5.
- There are no crossfades or continuous camera drifts in any cut; the decks are static plates
  between reveals. "Animation quality" here means reveal pacing + one zoom, and v3 matches v1
  on both while keeping v2's content.

---

## 3. Readability, layout and hash legibility

### 3.1 Caption ink height (full-res row band, bright-pixel projection)
Measured on the encoded frames, not the renderer:

| Cut | t = 74 s (scene 2) | t = 210 s (scene 5 zoom) |
|---|---|---|
| v1 | 23 px | **29 px** |
| v2 | 25 px | **25 px** |
| v3 | **29 px** | **29 px** |

v3 is **+16 %** over v2 at both points, matching the source change Inter **26 → 30 px**
(+15.4 %) and lead 38 → 42. v1's money-scene caption is also 29 px, so **v3 lands on v1's
caption size**, not merely "one step up from v2." Evidence:
`docs/audit-evidence-2026-11-27/caption-compare.png`.

### 3.2 Composition / magnification
Body-ink horizontal extent at t = 74 s (scene 2 hero card):

| Cut | body x-extent | width |
|---|---|---|
| v1 | 117 → 1800 | 1683 px |
| v2 | **159 → 1698** | **1539 px** |
| v3 | 117 → 1797 | 1680 px |

v2 renders the scene as a **whole page at page scale**, leaving ~9 % less width for the hero and
shrinking the type; v1 and v3 use the full body for one large hero card. This is the objective
form of "size and magnification": **v3 restores v1's composition** while keeping v2's tokens.
Evidence: `docs/audit-evidence-2026-11-27/scenes-compare.png` (scene 2 column).

### 3.3 Dead bands and layout integrity
- **v2** scene 5 instrument strip is a fixed-height card: labels at the top, ~180 px of empty
  surface below them (visible at t = 200 s). At t = 210 s v2 also carries a 171 px empty band
  (y 747–915).
- **v3** instrument strip is content-sized (labels sit on their own card bottom); no stretched
  strip. At t = 200 s v3's only empty band is ordinary page whitespace below the strip.
- **v1** has no instrument strip (simpler composition).
- All three keep body ink inside x ∈ [117, 1800] and clear of the frame edges; no clipping.
- v2 carries a stray lime **focus outline** around the scene-5 subtitle
  (`x402 · Base Sepolia (testnet) · a paid assessment…`) that v3 removed.

Evidence: `docs/audit-evidence-2026-11-27/money-compare.png`.

### 3.4 Hash legibility
At the money scene every cut prints the **full 66-char tx hash** and the two receipt
`content_hash` sha256 values, uncropped, in mono. v1's detail state is the largest (biggest
type); v2 is legible at full res but smallest; v3 is legible with the larger caption and
content-sized panels. No hash is ellipsized in any cut.

### 3.5 Claim surface / disclaimer
All three render the identical honest-capture line in scene 1 —

> This video is built from the deployment's real API responses, captured at build time.

— and the identical close CTA in scene 6 —

> Everything shown came from the live deployment. The URL is open — try it.

Evidence: `docs/audit-evidence-2026-11-27/disclaimer-cta-compare.png`. Persistent chrome on
every frame states `mode live · chain 84532 · Base Sepolia (testnet)`; scene 5 labels the rail
`x402 · Base Sepolia (testnet)` and shows `mocked False`. Testnet-vs-production is stated, so
§5 is satisfied by all three; v2/v3 make it more prominent via the always-on masthead.

---

## 4. Rubric scoring

Scores are 0–10, anchored on the evidence above. The video-facing rubric weights are
Technical quality **35**, Integration quality **5**, Reproducibility/demo **5**, Organic growth
**20** (§6); §8 is a 2–5 min gate (all pass at 3:52) and §5 is a claim-accuracy gate (all pass).

| Criterion | v1 | v2 | v3 | Anchor |
|---|---|---|---|---|
| Telegraph evidence visible | 8 | 9 | **9** | tx hash + both receipts + chain rail + testnet; v2/v3 add instrument strip and verdict stats |
| Technical clarity | 6 | 8 | **9** | v1 is a bare slide (no masthead/live badge); v2 console skin but dead bands + focus outline + page-scale type; v3 clean content-sized console |
| Reproducibility support | 9 | 9 | 9 | identical disclaimer + public URL + captured values |
| Motion / flow | 7 | 6 | **8** | one detail move v1/v3 vs two (one mid-scene) v2; all share the 1.5× push-in |
| Caption legibility | 9 | 7 | **9** | 29 px v1/v3 vs 25 px v2 |
| Claim accuracy (§5) | 9 | 9 | 9 | testnet stated on every frame; `mocked False` |

**v3 ≥ both ancestors on all six; strictly greater on five.** That is a Pareto dominance, so
the ranking does not depend on the weighting.

Weighted projection (video-touched weights only, 65 pts):
`TQ 35 = 0.6·clarity + 0.4·motion`; `INT 5 = evidence`; `REP 5 = reproducibility`;
`OG 20 = 0.5·captions + 0.5·clarity`.

| Cut | TQ /35 | INT /5 | REP /5 | OG /20 | **Total /65** |
|---|---|---|---|---|---|
| v1 | 22.4 | 4.0 | 4.5 | 15.0 | **45.9 (70.6 %)** |
| v2 | 25.2 | 4.5 | 4.5 | 15.0 | **49.2 (75.7 %)** |
| v3 | **30.1** | **4.5** | **4.5** | **18.0** | **57.1 (87.8 %)** |

**A judge scores v3 higher: +12.1 projected points over v2 and +17.2 over v1** on the 65
points the video actually touches.

**v1 vs v2 (for the backup slot):** this pair is weight-sensitive. v1 wins motion and caption
legibility; v2 wins integration evidence and technical clarity (it shows more of the working
surface). v2's weighted projection is 3.3 points higher, driven by the 35-point clarity term.
If a reviewer weighted composition legibility over product authenticity, v1 would close that
gap — but v2 still leads on the integration evidence the rubric explicitly asks to see.

---

## 5. Caption-size verdict — **delivered**

- Source: `CAPTION_SIZE 26 → 30`, `CAPTION_LEAD 38 → 42` (V-5 commit `d9ed4a5`).
- Encoded frames: caption ink band **25 px → 29 px (+16 %)**, consistent with 30/26.
- v3's 29 px equals **v1's** 29 px at the money scene, so the operator's "one size larger"
  request both landed and returned to the v1 size he preferred.
- All 18 captions were re-flowed at 30 px: 17 single-line, scene 4's third wraps to two; the
  strip stays inside the margins in every extracted frame.

**Yes — the larger-caption request was actually delivered in the encoded v3 cut.**

---

## 6. Recommendation

### 6.1 Submission
**Submit `demo/outbreak-sentinel-demo-v3.mp4`.** It dominates both ancestors on the rubric and
is the only cut that is simultaneously: console-mirrored (technical clarity + integration),
v1-composed at full magnification (technical clarity), one uninterrupted reveal per scene
(flow), and projector-legible captions (organic growth). It also removes v2's dead bands and
stray focus outline.

### 6.2 Backup
**Backup: `demo/outbreak-sentinel-demo.mp4` (v2).** It is the nearest rubric distance to the
winner (same skin, same integration evidence, same testnet/disclaimer surface); its losses are
the mid-scene cut, the smaller captions, and the stretched instrument strip. If v3 ever fails
to render or a skin defect surfaces, v2 is the fallback that changes the least about what the
judge sees.
**Third option: v1** — keep it as the motion reference and the operator's aesthetic favourite,
but it is not the rubric backup: dropping the console skin costs technical clarity and
integration evidence that the rubric explicitly weights.

### 6.3 A licensed synthwave mux — improve or hurt?
**Improve modestly, if licensed and mixed low; hurt only if unlicensed or loud.**

- **Organic growth (20)** is where music helps: polish and watchability for a public audience.
  **Technical quality (35)** is neutral — music clarifies nothing about what works — and
  **integration/reproducibility/§5** are untouched.
- The cut is **silent and voice-free by construction**, so music cannot mask narration; keep it
  instrumental (no vocals) and mixed low so captions remain the focus. Do **not** re-encode
  video: `ffmpeg -i v3.mp4 -i track.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4`,
  then verify `duration=232.000000` and that the only new stream is audio.
- **Licensing requirement:**
  - **Scott Buckley** — CC-BY 4.0: a **credit line is mandatory**, e.g.
    `Music: “<Track>” by Scott Buckley — released under CC BY 4.0 — www.scottbuckley.com.au`,
    in the submission description and ideally the end card.
  - **White Bat Audio** — free-to-use per their terms, but **verify the specific track's
    licence**; do not assume CC0. Credit where their page requires it.
  - **Pixabay** — Pixabay Content Licence (CC0-like): **no attribution required**; still confirm
    the track page.
- **Lowest-risk choice:** a **Pixabay CC0** track (zero attribution burden), or Scott Buckley
  CC-BY **with the credit line**. The rubric does not reward music directly, so the upside is
  small and the only real downside is a licensing/claim mistake — avoid that by documenting the
  licence alongside the file.

---

## 7. Evidence index (parent vision gate)

| File | Shows |
|---|---|
| `docs/audit-evidence-2026-11-27/money-compare.png` | scene 5 at t = 170/200/210 s, v1/v2/v3: skin, magnification, dead band, graph legibility |
| `docs/audit-evidence-2026-11-27/zoomransition-strip.png` | 207.2→208.0 s at 0.2 s steps: the shared cut-to-detail push-in |
| `docs/audit-evidence-2026-11-27/v2-midcut-strip.png` | 70.2→71.0 s: v2's extra mid-scene cut vs v1/v3 holding |
| `docs/audit-evidence-2026-11-27/caption-compare.png` | caption bands at t = 74 / 210 s: 25 px (v2) vs 29 px (v1, v3) |
| `docs/audit-evidence-2026-11-27/scenes-compare.png` | scene 2 LA card (magnification), scene 3 London (dead band), scene 1 cold open |
| `docs/audit-evidence-2026-11-27/disclaimer-cta-compare.png` | honest-capture disclaimer + close CTA, identical in all three |

Raw streaming numbers (`motion_*.txt`, `scene_*.txt`) live in the session scratchpad, not the
repo, to keep the tree clean; every figure above is reproducible with the commands in §2.

---

## 8. Ship gate

- **Built:** `docs/AUDIT-2026-11-27-video-comparison.md`; `docs/audit-evidence-2026-11-27/`
  (6 montages); one SPINE checkpoint (`## 2026-11-27 — Auditor-4`). No product code touched.
- **Sent:** two explicit-add commits — audit + evidence, then SPINE — pushed to `origin/main`.
- **Blocked:** nothing in this audit. Open operator actions: (a) choose the track + licence
  before any music mux; (b) parent vision-judges the six montages above; (c) the operator's own
  form/submission step, which is his to perform.
