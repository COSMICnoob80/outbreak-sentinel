# AUDIT 2026-11-26 — Auditor-3, final pre-submission gate

**Role:** standing auditor. Judgment only — no product code, no money spent, no
`git add -A`, no secrets printed. Writes limited to this file and one SPINE checkpoint.

**Moment:** Telegraph S2 deadline is **Dec 1, 23:59 UTC** (~5 days). Everything is
built. This is the last gate before the operator pastes the form and submits.

**Method:** every check below was run against the **live deployment**
(`https://outbreak-sentinel.onrender.com`) and the repo at `a849c52`, in the order a
judge would hit it. Read-only GETs only; the only chain calls were
`eth_getTransactionReceipt` / `eth_getTransactionByHash` on Base Sepolia (no spend).

---

## Verdict

> **Final gate: NO-GO — fix R1 (corrupt tx hash + wrong block in the form draft) first.**
> One-line copy edit, ~2 minutes. Once R1 is fixed, this ships as-is.

The product is real and live. The blocker is not the software — it is **one corrupted
copy-paste in the submission draft**, sitting inside the single block that literally
invites a judge to falsify it. Nothing else found is submission-stopping.

---

## 1. Submission draft vs live deployment — claim by claim

File: `demo/SUBMISSION-FORM-DRAFT.md` (untracked in git; verified directly).

### 1.1 Every URL returns 200 — PASS

| URL | Status | Time (warm) |
|---|---|---|
| `/telegraph/dashboard` | **200** | 1.84 s (109,719 B) |
| `/health` | **200** | 1.46 s |
| `/receipts` | **200** | 0.94 s |
| `/telegraph/status` | **200** | 1.65 s |
| `/telegraph/ledger` | **200** | 1.25 s |
| `/telegraph/stats` | **200** | 0.65 s |
| `/scoreboard` | **200** | 0.96 s |
| `/telegraph/assess` | **200** | 1.64 s |
| `/risk` | **200** | 11.1 s fresh, 14.4 s on a later render |
| GitHub repo `COSMICnoob80/outbreak-sentinel` | **200** | — |

All 10 live endpoints answered 200. `/risk` returns **34 cards** (14 bio-surveillance,
14 supply-chain, 6 wildfire), `engine: deterministic+narrator`, 19 cities.

### 1.2 The on-chain proof — **FAIL (blocking)**

The draft's `**Verified on-chain proof (checkable by anyone):**` block is wrong in **two**
independent ways:

**(a) The tx hash is corrupt — it does not exist on Base Sepolia.**

Draft (line 42 and again in the link on line 44):
```
0xac02bcbbe78e85760f3ae45400d457f750c9f10fd61c0fc9d06189fe84aa9c4f
```
Correct value (live `/telegraph/status`, `state/settlements.jsonl`, video):
```
0xac02bcbbe78e85760f3ae45400d457f750c9f0fd61c0fc9d06189fe84aa9c4cf
```

Character diff (`difflib`):
- an **extra `1`** inserted at index 39, and
- the trailing **`c`** (index 64) dropped.

Both strings are 66 chars, so length checks do not catch it. The RPC is decisive:

```
eth_getTransactionByHash(0xac02…c9f10fd61c0f…c4f)  → result: null
eth_getTransactionReceipt(0xac02…c9f10fd61c0f…c4f) → result: null

eth_getTransactionReceipt(0xac02…c9f0fd61c0f…c4cf) → status 0x1
    block 59597289 · to 0x036cbd53…dcf7e (USDC) · Transfer 10000 from 0x7b3654a6…f249
```

So a judge who clicks the "checkable by anyone" link lands on a dead transaction page.
This is precisely the falsification the draft's own "Integrity commitments a judge can
falsify in 2 minutes" section promises will hold up.

**(b) The block number belongs to a different transaction.**

Draft line 43 says `status 0x1, block 61335917-era settle` on the `0xac02bcbb` tx. On-chain,
`0xac02bcbb…c4cf` is **block 59,597,289**. Block **61,335,917** is a *different* tx,
`0x979515ea…7067`. The two txs were conflated. `demo/HACKATHON-SUBMISSION.md` (line 50) and
the video both have this right (59,597,289); only the form draft is wrong.

**Fix (R1):** replace both occurrences of the hash with
`0xac02bcbbe78e85760f3ae45400d457f750c9f0fd61c0fc9d06189fe84aa9c4cf` and replace
`block 61335917-era settle` with `block 59597289`. Copy from the live
`/telegraph/status` → `last_settlement.tx_hash` so they cannot drift again.

### 1.3 "Every finalized card gets a tamper-evident receipt" — **overclaim**

Draft line 28. The code files receipts only for **HIGH/CRITICAL** cards
(`publish.py:57` — `if card.get("risk_level") not in ("HIGH", "CRITICAL"): continue`).
Today's live render is 34 cards, **1 HIGH** → `/receipts` count **1**. So 33 finalized
cards get no receipt. `demo/HACKATHON-SUBMISSION.md:62` states it correctly ("A receipt is
filed when a HIGH/CRITICAL card finalizes"). **Fix (R2):** change "Every finalized card" to
"Every HIGH/CRITICAL card that finalizes".

### 1.4 "≤7 days of observable lead time" on every card — **not in the product**

Draft lines 67–70 claim "every card carries a bounded '≤7 days of observable lead time'".
There is **no such field or string anywhere**: not in `/risk` card keys
(`chart, city, confidence, disease, drivers, evidence_count, evidence_line,
illustration_hint, recommendation, region, risk_level, risk_score, sources, summary,
vertical`), not in the console, not in any `.py`/`.html`. What the engine actually has is a
**7-day evidence lookback** (a retrospective news window), which is not forward "lead time".
This is the Mission-06 headline and a sharp judge can falsify it against the API in one
request. **Fix (R3):** reword to the submission doc's honest framing — "the evidence window
is 7 days; a per-site spread/lead-time model is not in this build and we do not claim one",
and delete the claim that each card *carries* a lead-time bound.

### 1.5 MET Norway "kept serving 19/19" — stated as a past live event

Draft lines 54–56 assert the agent "kept serving 19/19 cities through a MET Norway fallback"
mid-competition. The fallback code ships (`app.fetch_weather`, commit `a3e1fba`), but per the
W-6 checkpoint the live fallback render was never observed (Open-Meteo recovered), and the
video presents it honestly as a **labelled replay** of Render's verbatim 429. Today
`/debug/weather` shows `providers: {open-meteo: 19}`, `failed: 0`. **Fix (R4):** soften to
"ships a MET Norway fallback, demonstrated in the video as a replay of Render's verbatim
429" rather than an observed live serve.

### 1.6 Settlement mode / mocked — PASS

`/telegraph/status`: `mode: live`, `is_live: true`, `settlement.mocked: false`,
`rail: "x402 (live)"`, `chain_id: 84532`, `last_settlement_source: "ledger"`. Matches the
draft. (The draft's phrase "receipts ledger seeded from `state/settlements.jsonl`" is a
term slip — it is the *settlement proof* that is seeded, not the receipts ledger — but it is
not false enough to block. Fold into R2/R3 copy edit.)

### 1.7 Other draft claims — PASS

- "19 cities across 3 hazard verticals" → `/risk.signals.cities = 19`, three verticals
  render. True.
- "Suite: 125 passing tests" → `pytest -q` → **125 passed, 3 warnings**. True.
- "tests/test_disease_evidence.py, 193 lines" → **193**. True.
- "3:52, 1920×1080" → `ffprobe` 232 s, 1920×1080. True.
- "receipts dedupe by stable card identity" → `publish._claim_identity`. True.

---

## 2. First 60 seconds (cold console) — **HIGH risk, partly unverified**

- **Warm**: console 200 in ~1.8 s, `/risk` 11 s fresh. In a real headless Chrome render the
  console reached **34 live cards**, badge `sysState = live`,
  `engine: deterministic+narrator`, `updated 0s ago`. It does look alive once data lands.
- **Cold-start notice — MISSING where the judge will see it.** The free-tier `~50 s wake`
  is documented in `README.md:121` and `demo/HACKATHON-SUBMISSION.md:17`, but the
  **form draft has no cold-start line at all**, and the console itself shows only a generic
  skeleton (`Loading live risk…` / `Contacting /risk for the fused city cards.`) — no mention
  that the first hit may wait ~50 s to wake and up to ~150 s to render.
  This is the "judge stares at a spinner with no explanation" failure the gate asked about.
  **Fix (R5):** add one line to the form draft next to the Console URL ("free tier wakes in
  ~50 s; first render up to ~150 s, then cached 5 min"), and, if a beat allows, one sentence
  in the console skeleton copy.
- **Cold-start measurement — measured, 2026-11-26T12:06:10Z** after a genuine 17-minute
  quiet idle (no traffic to the host while it slept):

  | Hit after idle | Status | Total | TTFB |
  |---|---|---|---|
  | `/telegraph/dashboard` (first hit — the wake) | **200** | **25.64 s** | 25.23 s |
  | `/health` (warm now) | **200** | 5.58 s | 5.58 s |
  | `/risk?disease=dengue` (first render, uncached) | **200** | 10.41 s | 10.40 s |

  The first render returned the full **34 cards**, `cached: false`,
  `engine: deterministic+narrator`. So the documented worst case (~50 s wake + ~150 s
  render) is conservative: from a real sleep the console HTML was served in **25.6 s**, and
  the card grid followed ~10 s later. That is a live first-60-seconds, not a dead spinner —
  **but it is still ~25 s of blank tab before any HTML**, which is exactly why R5 (state the
  wake time on the form) matters. Note two earlier probes read warm because audit traffic kept
  the dyno awake; only this quiet 17-minute idle probe is a true cold start.

---

## 3. Video — PASS with one staleness flag

`demo/outbreak-sentinel-demo.mp4`

- `ffprobe`: **232.0 s**, 1920×1080, h264, 30 fps, 6960 frames, 4,926,657 B. In the 120–280 s
  window. Video stream only, no audio (captioned) — acceptable, captions carry it.
- **8 evenly-spaced frames** (t ≈ 14.5, 43.5, 72.5, 101.5, 130.5, 159.5, 188.5, 217.5 s):
  all non-blank and in-family (`mean_lum` 15–24, `stdev` 8–24, ~480–1,560 unique colours);
  no white/flash/placeholder frame. **PASS.**
- **Scene 5 evidence hold (207.5–212 s) is fully legible** — extracted the frame at 210 s:
  full tx `0xac02bcbb…c4cf`, `rail x402 (live) · mocked False · 0.01 USDC · 10000 µUSDC`,
  `status 0x1 · block 59597289 · to 0x036cbd53…dcf7e`, and both receipt rows with their
  sha256 hashes, uncropped. **PASS.** (Video block 59597289 is *correct* for this tx; the
  form draft is the one that is wrong.)
- **Re-capture diff (`capture_video_data.sh`, read-only, run today) vs the committed
  snapshot** — what changed since the video was built:

  | Field | Video (committed snapshot) | Live today |
  |---|---|---|
  | cards / cities / engine | 34 / 19 / deterministic+narrator | 34 / 19 / deterministic+narrator |
  | level distribution | `LOW 29 · MODERATE 3 · HIGH 2` | `LOW 31 · MODERATE 2 · HIGH 1` |
  | receipts | `2 filed` (`rcpt-336283ecc0c4`, `rcpt-c8cd0f19221c` Cape Town HIGH 55) | **`1 filed`** (`rcpt-336283ecc0c4` only) |
  | hero LA wildfire | HIGH **65**, 5 sources | HIGH **65**, 5 sources (unchanged) |
  | news / city-scoped / social | 257 / 151 / 113 | 307 / 160 / 111 |
  | weather | 19/19 open-meteo | 19/19 open-meteo |

  *Headline is stable*: the LA wildfire HIGH 65 hero, the 34-card grid, the 19 cities and the
  settlement tx/block all match. *Two stale details*: the video says **"2 filed"** and shows a
  **Cape Town HIGH 55** receipt row that today returns **404** on the live deployment
  (`/receipts/rcpt-c8cd0f19221c` → 404; it was filed at runtime on 2026-11-26 12:34 and is not
  in the committed ledger or guaranteed to survive a redeploy — see §5). A judge who watches
  the video and then opens `/receipts` sees 1 row, not 2. **Flag (R6), not blocking** — the
  video is honestly captioned "captured at build time"; the mismatch is the volatile receipt
  count, not a fabricated headline.

---

## 4. Repo hygiene

| Check | Result |
|---|---|
| `.env` committed? | **No.** Never in history (`git log --all -- .env` empty); `.gitignore` covers `.env`, `.env.*`, `!.env.example`. `.render-env.txt` ignored. Only placeholders tracked (`TELEGRAPH_EVM_PRIVATE_KEY=0xyour_testnet_key`). **PASS.** |
| Secret scan of tracked files | No `gsk_…` / `sk-…` / hex-64 private key values. **PASS.** |
| `demo/screenshots/` present | 6 PNGs, all **1920×1080**. **PASS.** |
| Demo video tracked | `demo/outbreak-sentinel-demo.mp4` tracked. **PASS.** |
| License file | **MISSING.** `README.md:276` says "MIT" but there is **no `LICENSE`** file anywhere. **Fix (R7, cheap):** add `LICENSE` (MIT, `COSMICnoob80`). |
| README currency | Live URL + 50 s wake line present (`:119-121`). Two gaps: (a) README never links the demo video/screenshots; (b) `:84` says `curl localhost:8000/intel/llm` but the Run section never starts uvicorn (the working command is the one in `HACKATHON-SUBMISSION.md`). **Fix (R8).** |
| Working tree | `history/receipts.jsonl` dirty (7 local rows incl. runtime filings), `demo/SUBMISSION-FORM-DRAFT.md` untracked. Audit did **not** commit these. |

---

## 5. Receipt ledger durability — HIGH (fragility, not a false claim)

`/receipts` is served from `history/receipts.jsonl` (`app.py:1461`). That path is
**excluded from the image** (`.dockerignore`) and there is **no volume** in `render.yaml`.
Consequences observed live:

- The committed ledger (`HEAD:history/receipts.jsonl`) has **1** row
  (`rcpt-9575593f78c6`, Karachi, Oct 13) — that id returns **404** on the live deployment.
- The live `/receipts` returns **1** row (`rcpt-336283ecc0c4`, filed at runtime today
  16:13 PKT) which is **not** in the committed ledger.
- So the receipt count a judge sees depends on whether the dyno has re-rendered since boot:
  after a fresh redeploy `/scoreboard` can read `total_receipts: 0/1`, and receipts are
  re-filed (deduped by claim identity) on the first `/risk` render.

This is a survivability weakness, not a lie — but it makes the video's "2 filed" and the
receipt ledger non-deterministic across restarts. **Fix (R9, if a beat allows):** either add
a Render disk for `history/` + `state/`, or state on the form that the receipt ledger is
rebuilt from finalized cards at runtime (so `resolved: 0` / small counts are expected on a
fresh boot). Not submission-blocking.

---

## 6. Additional judge-visible inconsistency — LOW/MEDIUM

- **Console reads "weather 0" while 19/19 cities have weather.** The metric strip computes
  `weather = Number(s.weather) || 0` (`dashboard/index.html:1387`), but `/risk.signals` never
  emits a `weather` key — so the strip prints `news 307 · social 111 · weather 0` even though
  weather succeeded and cards carry rain/wind drivers. **Fix (R10):** count
  `signals.cities` (or add a `weather` count to `/risk.signals`). Cosmetic but a judge who
  cross-reads the strip against the cards will notice.
- **`/telegraph/stats`:** `wallet_usdc: null`, `wallet_error: "no live payer address on
  record"` on a fresh boot (pre-existing W-3 item 4). Both pages render it as unknown, not a
  fake number — acceptable, worth a one-line footnote if convenient.

---

## Ranked fix list

**Must fix before submit (NO-GO until R1):**
1. **R1 — form draft tx hash + block (blocking).** Replace `0xac02…c9f10fd61c0f…c4f` →
   `0xac02…c9f0fd61c0f…c4cf` (both occurrences) and `block 61335917-era` → `block 59597289`.
   Copy from live `/telegraph/status` so it cannot drift again. (~2 min)

**Should fix in the same copy edit (cheap, closes overclaims a judge can falsify):**
2. **R2** — "Every finalized card" → "Every HIGH/CRITICAL card that finalizes".
3. **R3** — drop "every card carries ≤7 days of observable lead time"; use the submission
   doc's honest 7-day *evidence window* wording.
4. **R4** — MET Norway: "ships a fallback (shown as a labelled replay)" not "kept serving".
5. **R5** — add the ~50 s wake / ~150 s first-render line next to the Console URL in the
   form draft.

**Nice-to-have (a beat each, not blocking):**
6. **R6** — note on the video page that the receipt count is a build-time snapshot (it was
   "2 filed"; live may show fewer after a redeploy).
7. **R7** — add an MIT `LICENSE` file (README already claims MIT).
8. **R8** — README: link the demo video/screenshots; fix the `localhost:8000` server line.
9. **R9** — persist `history/` + `state/` across redeploys, or disclose runtime rebuild.
10. **R10** — console "weather N" metric reads a key `/risk` does not send.

---

## What is genuinely strong (so the operator submits with confidence)

- Live, working, **34-card** multi-vertical product on a public URL, three verticals, 19
  cities, `engine: deterministic+narrator`, citations on every card's sources.
- **Real x402 settlement** verifiable on Base Sepolia: three txs confirmed `status 0x1`,
  each a genuine 10,000-unit (0.01 USDC) USDC `Transfer` from burner
  `0x7b3654a6…f249` — blocks **59,597,289**, **61,335,917**, **48,407,418**.
  `mocked: false`.
- Honest framing throughout the long-form docs and the video (deterministic engine, LLM
  narrator only, testnet boundary, RSS ingestion, 3-of-7 verticals render).
- Suite **125 passed**; geography/evidence gates tested; no secrets committed.

The gap between this and GO is a **copy-paste**, not the build.

---

**Ship gate**

- **Built:** everything. Live 34-card, 3-vertical console; real x402 settlement on Base
  Sepolia; 232 s captioned video with legible on-chain evidence; 125 passing tests; 6 form
  stills. Nothing needs building for this submission.
- **Sent:** nothing yet — the form has not been submitted and the bounty repo is not yet
  starred from `COSMICnoob80`. Both are the operator's, not the auditor's, to do.
- **Blocked:** the submission itself, on **R1** — the form draft's tx hash and block number.
  Both are wrong in `demo/SUBMISSION-FORM-DRAFT.md`; the correct values are one paste away
  from live `/telegraph/status`. R2–R5 are the same copy edit. Nothing else blocks GO.

