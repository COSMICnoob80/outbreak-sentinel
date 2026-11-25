# AUDIT-2026-11-25 — Global credibility re-audit of the FIXED state

**Auditor:** AUDITOR-2b (standing project auditor — judgment only, no product changes)
**Audit time:** 2026-11-25, ~19:00–19:20 PKT
**Repo state:** `6b0790f` (`docs(spine): checkpoint soldier D-2`); working tree had
`dashboard/index.html` (Soldier D-3) and `history/receipts.jsonl` already modified at
session start
**Live instance:** https://outbreak-sentinel.onrender.com
**Prior audit:** `docs/AUDIT-2026-11-22.md` — `Readiness: 45/100`
**Deadline:** Dec 1 2026 23:59 UTC (~6 days)

**Method.** Read SPINE, the prior audit, `config.yaml`, `app.py`, `outbreak_sentinel.py`,
`publish.py`, `receipts.py` and the whole submission pack. Ran the suite. Issued **six
read-only live renders** (`/risk` with `refresh=1`, three disease/city variants) plus
`/scoreboard`, `/receipts`, `/receipts/{id}`, `/telegraph/status`, `/telegraph/stats`,
`/telegraph/intents`, `/intel/llm`, `/cities`, and the four HTML surfaces. Ran one local
instance on `127.0.0.1:8007` (killed; `8001` never touched) as a control. Verified one
settlement tx on Base Sepolia with `eth_getTransactionReceipt`. **No paid request was
fired; no money was spent.**

---

## Verdict first

`Readiness: 56/100 — the false-HIGH defect is genuinely fixed and the former BLOCKING
items B1/B3/B4 and HIGH items H6/H8/H9 are live and true, but the live deployment now has
a weather outage that strips half the wildfire cards' stated drivers, mints duplicate
receipts for one claim, and still has no video or organic-growth evidence.`

Against the prior `45/100`, that is **+11**. The engineering is no longer the problem.
What caps the score is one live-render defect plus the 20% of the rubric no code can earn.

---

## Axis scorecard

| # | Axis | Score | One-line evidence |
|---|---|---|---|
| 1 | Evidence integrity sweep | **7/10** | The disease-term gate holds on every card in 6 renders — zero other-disease contamination survived. But the LA wildfire driver says "9 reports" while its evidence line and links say 5, Vancouver is MODERATE on two non-incident stories, and **live weather is dead** (`cities: 0` on 3/3 probes) so wildfire cards lose their weather drivers. |
| 2 | Claim credibility | **7/10** | Causal paid intelligence, live receipts and seeded settlement are now **true in code and on the live wire**. Overclaims left: test count (docs say 94/95, actual **109**), "days-to-impact per site" has no code, and `publish.py`'s idempotency claim is falsified by two live duplicate receipts. |
| 3 | Demo readiness | **7/10** | All four parent checkboxes pass on the live URL: 34 global cards with honest levels, LA wildfire **HIGH** with 5 real sources, `/receipts` returns 2 receipts, `/telegraph/status` seeds a real verified tx. Deductions: empty sparklines and missing weather drivers live; a redeploy wipes the ledger. |
| 4 | Submission completeness | **4/10** | Live URL, Track 01, missions 06/11 and the correct 35/25/10/5/5/20 rubric are all in the submission. Still missing: **video**, screenshots, organic-growth evidence, starred-bounties username, and the days-to-impact number mission 06 asks for. |

---

## 1. Evidence integrity sweep — 7/10

### 1.1 The disease-term gate: verified holding

The defect this audit was dispatched to re-check is real and fixed. Across six live
renders (dengue, malaria, London-filtered dengue) I classified **every** cited headline.

**Sweep result: 13 cited headlines total — 0 other-disease, 0 unrelated.**

| City | Vertical | Level / score | Cited headline(s) | Classification |
|---|---|---|---|---|
| **London** | bio / Dengue | LOW 20 | "UK steps up trapping efforts after mosquitoes that can spread dengue breed in London homes — Yahoo" | **on-disease-local** (vector story, true positive) |
| **Los Angeles** | wildfire | HIGH 55 | Guardian "Man accused of sparking deadly Los Angeles wildfire found guilty"; 4× Sacramento Bee "Breaking: New wildfire reported in Los Angeles County on Nov 20/22/23/24" | **on-hazard-local** (5/5) |
| **Sydney** | wildfire | LOW 20 | DW.com "In pictures: Australia 'mega fire' blankets Sydney with smoke" | **on-hazard-local** |
| **Cape Town** | wildfire | MODERATE 40 | IQAir De Hoop–Malgas–Potberg fire; EWN "Fifteen houses ablaze… 25,000 hectares Western Cape"; Cape Town ETC ×2 | **on-hazard-regional** (4/4, all Western Cape) |
| **Vancouver** | wildfire | MODERATE 30 | "Vancouver filmmaker screening award-winning wildfire doc"; "Vancouver company says its predictive technology can reduce lightning strikes that spark wildfires" | **on-vocabulary, not an incident** (see 1.2c) |
| *13 other bio cities* | bio | LOW 0 | — | 0 sources (honest empty) |
| *14 supply-chain cities* | supply-chain | LOW 0 | — | 0 sources (honest empty) |

The ebola and legionnaires' headlines that caused the original false London HIGH are
**absent** from every render. A raw string sweep of the full payload for `ebola`,
`legionnaire`, `covid`, `lassa`, `nipah`, `zika`, `h5n1`, `polio`, `tuberculosis`
returned **0** hits (the two `hiv` matches are base64 fragments inside Google News
redirect URLs, not headlines).

The gate is enforced in one place — `_city_topic_news` → `_distinct_city_news` — so a
filtered-out headline cannot reach the score, `evidence_count`, the driver text, the
`evidence_line`, or `sources`. `tests/test_disease_evidence.py` (15 tests) pins the exact
London scenario. **This axis is closed.**

### 1.2 Live defects the sweep surfaced

**(a) Driver count contradicts the rendered evidence — on the hero card.**
On the live LA wildfire card:

- `drivers[0].text` = **"9 city-specific wildfire reports in 7 days"**
- `evidence_line` = **"5 city-specific wildfire reports in the last 7 days"**
- `sources` rendered = **5 links**

Mechanism: `rule_based_vertical_risk(len(items), …)` scores on the full distinct set,
then `card["sources"] = [...][:5]` truncates the links. A judge reading the driver and
then counting links gets 9 vs 5. It is an honesty defect of exactly the class this
project exists to avoid, on the single card the demo points at. Bio cards are unaffected
because their evidence sets are ≤5.

**(b) Live weather is dead — wildfire cards lose half their stated drivers.**
`signals.cities` was **0 on three consecutive live probes**, and every wildfire card
returned `chart: []`. Locally, on the same commit, `cities: 19` and every card has a
7-point chart. Live vs local on the same payload:

| LA wildfire | Live | Local (127.0.0.1:8007) |
|---|---|---|
| level / score | HIGH **55** | HIGH **65** |
| drivers | "9 city-specific wildfire reports" | "9 … reports" + **"Dry 7-day outlook: 1.5 mm rain"** |
| chart points | **0** | **7** |

So the deployed hero card is 10 points weaker than the code the docs describe, carries no
weather driver, and draws no sparkline. `api.open-meteo.com` answers my audit host in
5.5 s with all four requested daily keys, so this is specific to Render's egress — the
same class of failure Soldier W-1 documented on 2026-11-20 and believed it had made
visible. The `weather city=… error=…` WARNING line does exist (`app.py:110/126`), but
Render's logs are not reachable from here, so the cause is **unproven** — only the
symptom is certain. Because a *failed* grid is deliberately not cached, every render
re-attempts and re-fails.

**(c) Vancouver MODERATE 30 on two non-incident stories.**
A film screening and a startup's marketing claim both contain the word "wildfire", so
both pass `title_mentions_city` + `_vertical_topic`. Two reports clear the 30-point band.
`MODERATE` is defensible under the current vocabulary, but a documentary screening is not
wildfire hazard. Smallest of the three findings, clearest fix: require an incident term
(burning, evacuated, contained) and not just the hazard word.

---

## 2. Claim credibility re-audit — 7/10

Verified against live behaviour and code on audit date.

| Claim (source) | Verdict | Evidence |
|---|---|---|
| Live deployment answers (SUB:11–15) | **verified** | `/health` 200 in 1.3 s; console 200 / 109,198 B; `/ledger`, `/assess`, `/buying-layer` all 200 |
| 109 tests pass | **verified** | `pytest -q` → **109 passed, 3 warnings in 9.07 s** |
| Every HIGH/CRITICAL card files a receipt (README:19, ONE-PAGER:23) | **verified — newly true** | Live `/scoreboard` → `{"total_receipts":2}`; `/receipts` lists LA wildfire HIGH; `/risk` returns per-card `receipts: [...]`. The former BLOCKING B3 is genuinely closed. |
| The purchased answer is a cited driver on the card (SUB:7, ONE-PAGER:40) | **verified in code** | `_paid_intelligence(proof)` → `paid_intelligence` on the response; an empty answer yields `status:"unavailable"` and no driver, never an invention. Not re-run live (no spend) — the code path and W-3's recorded probe agree. |
| Settlement proof visible on a fresh boot (H6) | **verified** | `/telegraph/status` → `last_settlement_source: "ledger"`, tx `0xac02bcbb…c4cf`; that tx is **on-chain** (status `0x1`, block **59,597,289**, to the USDC contract `0x036C…dCF7e`) — matches SUB:48 exactly |
| Load-bearing rubric 35/25/10/5/5/20 (SUB:32, FIT:15) | **verified** | Consistent across submission, one-pager and fit table |
| Track **01 — Apps & Agents** (SUB:3) | **verified** | The former "Track 03" mislabel is gone from the submission path |
| "Test suite → 94 passed" (SUB:40) / "95 passed" (SHOTLIST:52) | **overclaim (stale)** | Actual **109**. A judge running the command sees a *better* number than the doc, but the doc is still wrong. |
| "The wildfire vertical answers **days-to-impact per site**" (SUB:29) | **overclaim** | `grep -rn "days.to.impact"` hits only in **docs**. No field, no computation, and no card carries a days-to-impact number. Mission 06's literal ask is unimplemented. |
| "Rebuilding the same grid cannot append the same call twice" (`publish.py:23`) | **falsified** | Two live receipts exist for the *same* LA claim, differing only in driver count: `rcpt-0b9a629097ac` (8 reports) and `rcpt-a7c3b0f99663` (9 reports). The claim hash includes the volatile count, so every re-render that sees a different count mints a new receipt. `/scoreboard` therefore reports **2 calls for 1 event**. |
| "7 verticals registered, 3 render" (ONE-PAGER:5,50) | **verified** | Accurate and no longer overstated |
| "Free Groq fusion" | **not present** | The stale claim is gone; docs name `z-ai/glm-5.3-flash`, and `/intel/llm` → `{"provider":"commandcode","model":"z-ai/glm-5.3-flash","ok":true}` |
| "~136 intents" (ONE-PAGER:62) | **verified** | `/telegraph/intents` → `count: 136` |
| "Every paid ask settles 0.01 USDC on Base Sepolia" | **verified** | chain 84532, USDC `0x036C…dCF7e`, tx confirmed above |
| Wallet balance shown on the console (prior NICE #11) | **still overclaim-adjacent** | `/telegraph/stats` → `wallet_usdc: null`, `wallet_error: "no live payer address on record"` |

**Net:** the narrative claims that carried the product — the ledger, causality, the seeded
settlement — are now the *most* true things in the repo. That is the reverse of the
2026-11-22 finding, and it is a real turn. What remains is one stale number, one
unimplemented mission metric, and one ledger-integrity bug.

---

## 3. Demo readiness re-score — 7/10

The four parent checkboxes, judged by what a stranger sees in five minutes:

| Check | Result | Evidence |
|---|---|---|
| Global city cards with honest levels | **PASS** | 34 cards: 14 bio + 14 supply-chain + 6 wildfire. 31 LOW, 2 MODERATE, 1 HIGH. London dengue LOW 20 with its one true vector source; 13 bio cities honestly empty. |
| A wildfire HIGH card with real sources | **PASS, weakened** | LA HIGH/55, 5 real cited stories (Guardian + 4 Sacramento Bee), filed to the ledger as `rcpt-a7c3b0f99663`. Weakened because the dry-outlook driver and sparkline are missing live (1.2b). |
| Receipts at `/receipts` | **PASS** | `{"count":2}`, both LA wildfire HIGH, `status: OPEN`, sha256 content hashes, detail route 200 |
| A settlement tx at `/telegraph/status` | **PASS** | seeded from the ledger, real 10,000 µUSDC transfer, explorer URL present, `mocked: false` |

Console honesty greps on the served shell still clean: `unspecified hazard` **0** (the D-2
fix held), `PAKISTAN` / `OTHER CITIES` both present, `SETTLED ON-CHAIN` present, one
labelled `demo data` fallback, and the inline script passes `node --check` (61,237 B).

**Deductions:** sparklines are empty live, so the console shows `no series` where the docs
promise a rain-forecast strip; the engine value reads `deterministic` in the instrument
strip; and the biggest risk to a recorded demo is that **a Render redeploy wipes
`history/receipts.jsonl`** (excluded in `.dockerignore`, no volume mounted), so
`/receipts` returns to empty until the next HIGH card finalizes.

---

## 4. Gap list for the remaining days

### BLOCKING

1. **No demo video.** The rules ask for 2–5 minutes; the repo has five doc files and
   **zero** media (`find` for mp4/webm/mov → none). 5% reproducibility and the whole
   organic-growth story ride on this. Nothing else in the entry is blocked.
2. **Live weather outage.** `cities: 0` on 3/3 probes strips the dry/wind drivers and the
   sparklines from every wildfire card — including the HIGH card the demo is built
   around. Either fix Render egress (diagnose from the WARNING logs) or record against a
   host that has weather and say so plainly.

### HIGH

3. **Duplicate receipt minting.** The claim hash includes the volatile report count, so
   one LA event became two receipts (`0b9a…` / `a7c3…`). Key the hash on
   city+subject+level (+ a day bucket), not on the driver text.
4. **Driver count vs rendered links.** LA says "9 reports" and shows 5. Truncate the
   driver to `len(sources)`, or render every counted link.
5. **Receipts do not survive a redeploy.** `.dockerignore` excludes the ledger and no
   volume is mounted; on a free instance a redeploy is not exotic.
6. **Mission 06's "days-to-impact per site" has no implementation.** Either add a
   days-to-impact estimate to wildfire cards or stop claiming mission 06 in that form.

### NICE

7. **Test-count drift** — SUB:40 says 94, SHOTLIST:52 says 95, actual 109.
8. **Vancouver MODERATE on a film screening** — require an incident term, not just the
   hazard word.
9. **No screenshots** anywhere in the repo; the submission form and README both want them.
10. **Organic growth: zero evidence** (20 of 100 rubric points). No dated public posts, no
    starred-bounties username recorded.
11. **`wallet: —`** still resolves to `no live payer address on record`
    (`/telegraph/stats` → `wallet_usdc: null`).

---

## 5. Rubric estimate (calibration, not a prediction)

| Weight | Criterion | Est. | Why |
|---|---|---|---|
| 35% | Technical / mainnet readiness | 26/35 | Causal purchase, live receipts, seeded settlement, deterministic engine with a disease gate — genuinely strong. Lost: weather outage live, duplicate receipts, driver/link mismatch. |
| 25% | Commercial viability | 18/25 | Coherent buyer, replacement and unit economics; honest about testnet |
| 10% | Adoption | 4/10 | Self-serve assess, public ledger, API — but no real users |
| 5% | Integration | 4/5 | Telegraph REST seam + own service + Render + PWA |
| 5% | Reproducibility | 3/5 | Green suite + blueprint in repo, but no video |
| 20% | Organic growth | 0/20 | Nothing dated, public, or reproducible by a stranger |

**≈ 55–56 / 100 → `Readiness: 56/100`** (prior: 45/100).

The 70/100 threshold is reachable on paper — but only by spending the 20 organic-growth
points, which cannot be coded.

---

## 6. Top three actions for the remaining ~6 days

1. **Record the 2–5 minute video against a host that has weather.** Film the LA wildfire
   HIGH card *with* its dry-outlook driver and sparkline (local `127.0.0.1:8001` is fine
   and the docs already give the command), the bio grid with honest LOW empties, a scroll
   of `/receipts`, and `/telegraph/status` showing the verified tx. Video is the last
   BLOCKING item and it costs one recording session.
2. **One small integrity beat: weather diagnosis, receipt dedupe, count reconciliation.**
   Read Render's `weather city=… error=…` lines and fix or document the egress; change the
   receipt claim hash so one event cannot file twice; make the LA driver say 5 when 5 are
   shown. Each is judge-falsifiable today and each is cheap.
3. **Spend the organic-growth points.** Three dated public posts (X / GitHub / the
   Telegraph Discord), each with a reproducible request and an invitation to try it; star
   the bounties repo and record the username in the submission. That is the only path to
   20 rubric points and the only evidence a judge can independently check.

---

## Appendix — audit hygiene

- No product code, config, dashboard, receipt logic or test was modified.
- The local control instance ran on `127.0.0.1:8007` only and was killed; the pre-existing
  listener on `8001` was never touched.
- My one local render appended two receipt rows (`19:07:49`); **exactly those two were
  removed** and `history/receipts.jsonl` was restored to its pre-session 5 rows. No live
  ledger row was written — every live probe was a read-only `GET`.
- **No paid request was fired. No money was spent.**
- No `.env` contents or secrets are printed here.
- Raw endpoints used: `/health`, `/risk` (×6), `/scoreboard`, `/receipts`,
  `/receipts/{id}`, `/telegraph/status`, `/telegraph/stats`, `/telegraph/intents`,
  `/telegraph/dashboard`, `/telegraph/ledger`, `/telegraph/assess`,
  `/telegraph/buying-layer`, `/intel/llm`, `/cities`, `eth_getTransactionReceipt`
  (Base Sepolia), `api.open-meteo.com`.
