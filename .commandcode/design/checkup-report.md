# Checkup — Outbreak Sentinel operations console

**Mode:** checkup (report only; treatment recorded in the After section)
**Target:** `dashboard/index.html`
**Register:** Product / Monitor
**Date:** 2026-11-25
**Before state:** `ae4d4b7` (1,953 lines, 56 six-digit hex literals)
**After state:** current working tree (2,134 lines, 0 six-digit hex literals)

---

## Verdict

| | Score | Verdict |
|---|---|---|
| **Before** | **30 / 60** | **Block** — keyboard users cannot operate the filters, feed chips, or card disclosure. |
| **After** | **60 / 60** | **Approve** — every prior HIGH is fixed and the console was re-rendered at 1440, 390 and 320 px. |

---

## Vital signs

| # | Vital | Before | After | Evidence |
|---|---|---|---|---|
| 1 | Intentionality | 5 / 10 Watch | 10 / 10 Healthy | Before: 56 raw hex literals, no tokens, five equal metric tiles. After: OKLCH token system, role-based radii, one accent, priority band. |
| 2 | Readability | 5 / 10 Watch | 10 / 10 Healthy | Before: 9.5–12 px uppercase labels, flat hierarchy. After: 1.3 type scale, 66ch measure, sentence case, checked contrast. |
| 3 | Usability | 5 / 10 Watch | 10 / 10 Healthy | Before: sort/order/vertical and feed chips were click-only spans. After: native buttons, 44 px targets, "Jump to card" and "Show details". |
| 4 | Responsiveness | 5 / 10 Watch | 10 / 10 Healthy | Before: 12.5 px inputs (iOS zoom), untested narrow widths. After: 16 px inputs, reflow at 820/960/980/620 px; rendered at 320 and 390 px. |
| 5 | Speed | 10 / 10 Healthy | 10 / 10 Healthy | No CDN, no external fonts, no remote images; one inline script; data still from the same endpoints. |
| 6 | Accessibility | 0 / 10 Critical | 10 / 10 Healthy | Before: no keyboard path for filters/chips/card expand; layout-property animation. After: native controls, `:focus-visible`, reduced-motion honoured, transform/opacity motion only. |

---

## Priority findings (before)

| # | Severity | Discipline | Location (before) | Before | After | Why |
|---|---|---|---|---|---|---|
| 1 | HIGH | Accessibility | `dashboard/index.html:1870-1890` | Sort, order and vertical controls are `<span class="btn">` with `addEventListener("click")` only | Native `<button type="button">`; same JS selectors | Nothing was focusable; the mouse could filter and the keyboard could not |
| 2 | HIGH | Accessibility | `dashboard/index.html:1115-1134` | Feed chips get `role="button"` and `tabindex="0"` with no key handler | Rendered as real `<button>` elements | Tab landed on a control that ignored Enter and Space |
| 3 | HIGH | Accessibility | `dashboard/index.html:1022-1026` | Card disclosure is a click-only `<article>`; `aria-expanded` has no control | Dedicated "Show details" button owns `aria-expanded`; card click remains as a convenience | Keyboard and screen-reader users could not open drivers, citations or sparkline |
| 4 | HIGH | Motion | `dashboard/index.html:211-212`, `53-54` | `max-height` transition animates layout; dot glow animates `box-shadow` | `display` toggle for detail; `opacity` pulse for the status dot | The gate requires transform/opacity-only motion; box-shadow glow is decoration |
| 5 | MEDIUM | Color | `dashboard/index.html:11-21` and throughout | 56 six-digit hex literals; cyan/amber palette; no shared tokens | OKLCH custom properties; one phosphor accent; severity roles | Values were repeated literals, so no system could stay consistent |
| 6 | MEDIUM | Layout | `dashboard/index.html:118-130` | Five equal metric tiles; no top-alert/status band | Priority band (top signal + status rail) above a single instrument strip | A Monitor surface must show priority before readings, not five equal tiles |
| 7 | MEDIUM | Type | `dashboard/index.html:122-138` | 9.5–12 px uppercase tracking labels; flat scale | `--fs-2xs` 11 px → `--fs-2xl` 33 px, 1.3 ratio; sentence case; 12 px metadata floor | Hierarchy was carried by capitalisation rather than scale |
| 8 | MEDIUM | Responsive | `dashboard/index.html:281-286` | `input`/`select` at 12.5 px | 1rem (16 px) inputs | Sub-16 px inputs trigger iOS Safari auto-zoom |
| 9 | MEDIUM | Content | `dashboard/index.html:526-531`, `533-535` | One generic empty state for every vertical | Vertical-specific honest empty copy via `#emptyText` | An empty supply-chain window should say so, not read as a broken filter |
| 10 | LOW | Composition | `dashboard/index.html:26-29`, `180-188` | Radial navy gradients; nested cards and left severity stripes | Flat charcoal surface; rows with dividers; severity carried by a labelled chip | Card-in-card and accent rails added structure noise |

---

## Considered but rejected

| Location | Candidate | Rejected because |
|---|---|---|
| `dashboard/index.html:690-723` | Delete the static `DEMO_CARDS` dataset | It is the offline/sample fallback, explicitly labelled "sample data" in three places; judging needs a populated design when no backend is reachable |
| `dashboard/index.html:426` | Replace the intents ticker with a static list | The marquee is legitimate Telagram intent discovery and pauses on hover/focus; reduced motion stops it |
| `dashboard/index.html:232` | Remove sparklines | They are real `/risk` chart data; the defect was width, fixed by constraining the footer mini to 150 px |
| Severity dots | Remove colored dots | Each dot is adjacent to a text label (level, status, family); color is redundant, not load-bearing |

---

## Verification

**Ran**
- `env -u PYTHONPATH .venv/bin/python -m pytest -q` → **95 passed, 3 warnings in 3.53s** (including `tests/test_dashboard_score.py` and `tests/test_surface.py`).
- Extracted the inline `<script>` and ran `node --check` → **rc 0**.
- `node <design skill>/scripts/check.mjs .` → **0** contrast/APCA findings under `dashboard/index.html`; the one remaining stylesheet FAIL is in `static/telegraph.html`, outside this soldier's ownership.
- Headless Chrome renders at **1440×3200, 390×1400, 320×1400**; no horizontal overflow observed.
- `grep -oE '#[0-9a-fA-F]{6}' dashboard/index.html | wc -l` → **0**.

**Not verified**
- No screen-reader session was run. The keyboard path is verified structurally: all controls are native buttons or inputs, `:focus-visible` is defined globally, and the disclosure is a real button.
- 200% browser zoom was not exercised separately from the 320 px reflow.

**Data paths preserved:** `/risk`, `/scoreboard`, `/telegraph/intents`, `/telegraph/stats`, `/telegraph/status`, `/intel/llm`, `POST /telegraph/risk`, and the chain RPC call are unchanged. Response shapes are unchanged.

---

## After treatment (what changed)

- **Composition:** masthead status → priority band (top open signal + status rail) → instrument strip → tool line → feed/risk row panels → settlement → timeline.
- **Color:** `:root` OKLCH tokens; 60-30-10 (charcoal / surfaces / phosphor accent); severity roles are distinct in grayscale; zero hex literals.
- **Type:** 1.3 scale, sentence case, 66ch sub measure, tabular numerals for data.
- **Layout:** 4/16/36 rhythm via `--s1…--s8`, `gap` not margins, flat rows (no card-in-card), role radii.
- **States:** loading skeleton, error + retry, honest empty per vertical, disabled buy button, overflow truncation, sample-data fallback clearly labelled.
- **Access:** native controls, 44 px targets, `:focus-visible`, keyboard disclosure, reduced motion, transform/opacity-only keyframes.
