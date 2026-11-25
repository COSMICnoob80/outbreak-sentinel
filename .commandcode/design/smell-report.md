# Smell — Outbreak Sentinel operations console

**Mode:** smell (report only; treatment recorded in the After section)
**Target:** `dashboard/index.html`
**Register:** Product / Monitor
**Date:** 2026-11-25

---

## Verdict

| | Score | Verdict |
|---|---|---|
| **Before** | **1 / 10** | **IDENTITY FAILURE** — nine confirmed tells clustered into one generated-dashboard lane. |
| **After** | **10 / 10** | **CLEAN** — no confirmed tell remains in the console. |

---

## Odor table (before)

| Odor | Detected | Evidence |
|---|---|---|
| Tech gradient | **yes** | Two navy radial gradients at `:26-29` (`#16233d`, `#131c30`) |
| Generic tech hue | **yes** | Cyan `#38bdf8` as the primary identity, amber as secondary |
| Feature tile grid | **yes** | Five equal metric tiles at `:118-130` |
| Accent rail | **yes** | Colored left border on every risk card at `:180-188` |
| Unearned blur | no | No `backdrop-filter` |
| Stat monument | **yes** | Equal-number metric strip with no dominant reading |
| Icon topper | no | Glyphs sit in card footers, not above headings |
| Bounce everywhere | no | No elastic easing |
| Default type | no | System stack is legitimate for product UI |
| Center stack | no | Two-column working grid |
| Untokenized values | **yes** | 56 six-digit hex literals and repeated raw sizes |
| Card-ification | **yes** | Panel > card > receipt-block all bordered surfaces |
| Pill-shaped everything | **yes** | Badges, chips, pills, segments all `999px` |
| Section eyebrow labels | **yes** | Uppercase tracked micro-labels above nearly every block |
| Broken/fabricated media | no | No remote images, fonts or CDNs |

**Confirmed tells: 9 → 1 / 10.**

---

## Dominant smell and root reflex

**Dominant smell:** the page could be any dark SaaS monitoring dashboard. **Root reflex:** every surface was assembled independently from safe defaults (cyan accent, navy gradient, rounded cards, pill chips, uppercase eyebrows) instead of derived from the work: bio-surveillance plus on-chain verification.

The fix is a direction change, not a coat of paint. A stranger should not be able to guess the palette from "dashboard" alone.

---

## Priority findings

| # | Severity | Discipline | Location (before) | Before | After | Why |
|---|---|---|---|---|---|---|
| 1 | HIGH | Accessibility | `:1870-1890`, `:1115-1134`, `:1022-1026` | Mouse-only spans and a click-only card | Native buttons and a real disclosure control | Generic structural smell and an access failure travel together |
| 2 | HIGH | Motion | `:211-212`, `:53-54` | Layout transition + box-shadow glow | `display` toggle + opacity pulse | Motion was decoration, not state |
| 3 | MEDIUM | Color | `:11-21` | 56 raw hex literals, cyan identity | OKLCH tokens, phosphor accent, tinted neutrals | The palette was the domain's first reflex |
| 4 | MEDIUM | Layout | `:118-130` | Five equal tiles | Priority band + single instrument strip | No hierarchy; every reading had equal weight |
| 5 | MEDIUM | Color | `:180-188` | Left severity stripes | Labelled severity chip + colored score | A colored rail simulates structure rather than encoding it |
| 6 | MEDIUM | Layout | `:135-322` | Card inside panel, receipt block inside receipt | Flat rows with dividers | Nested cards are never right |
| 7 | MEDIUM | Type | `:122-138` | 9.5–12 px uppercase tracking | 1.3 scale, sentence case, 12 px floor | Capitalisation was doing hierarchy's job |
| 8 | LOW | Color | `:57-82`, `:143-148`, `:343-345` | Pill radius on most controls | One pill role (status badge); 6 px controls | Full rounding was a house reflex |

---

## Considered but rejected

| Location | Candidate | Rejected because |
|---|---|---|
| System font stack | Call it the reflex font | Product UI may use the system stack; there is no loaded web font and no evidence of a default-type smell |
| `:690-723` | Call static sample data a "fabricated media" tell | It is labelled sample data in the status badge, pill and footer; no remote asset is loaded |
| `:105-107` | Call the marquee an autoplay tell | It pauses on hover/focus and stops under `prefers-reduced-motion` |
| `:433` | Remove the intent ticker entirely | It carries real Telegraph discovery data; the smell was styling, not existence |

---

## After treatment

The console now reads as an instrument panel, not a template:

- **Hue with a reason:** phosphor signal green (`oklch(0.862 0.190 128)`, #ade84f), the colour of lab/oscilloscope instrumentation and "verified" state, on a charcoal tinted toward the same hue. Not cyan, not indigo, not a tech gradient.
- **One accent role:** accent is reserved for live/verified state and the primary action; risk severity uses four separate roles.
- **Composition from work:** priority alert and status rail lead; readings follow in a single strip; feed and risk rows scan as lists.
- **Type:** system UI at a 1.3 scale; monospace is used only for machine data (scores, hashes, timestamps), not as a "hacker" costume.
- **No nested cards, no accent rails, no pill-everything, no uppercase eyebrows, no glow.**

**Remaining reflex warning from `check.mjs`:** a global "pill radius on 8 selectors" note counts other, untouched `static/` pages; the console itself uses full rounding for exactly one role (status badge).
