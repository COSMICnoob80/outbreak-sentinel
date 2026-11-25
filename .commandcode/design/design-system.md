# Design system — Outbreak Sentinel operations console

**Register:** Product (Monitor)
**Source of truth:** `dashboard/index.html` `:root` block. Every token below is a live CSS custom property consumed by the interface; nothing here is documented without a real token.
**Preview:** `design-system.html`

---

## Why this palette

Bio-surveillance plus on-chain verification reads as an **instrument panel**: a lab monitor or oscilloscope. The accent is **phosphor signal green**, the colour of instrument traces and "verified" state. Surfaces are charcoal tinted toward the same hue (chroma ≤ 0.014) so the neutrals feel related rather than dead grey. This deliberately avoids the two reflex answers for a monitoring dashboard: cyan-on-dark and indigo gradients.

**Commitment level:** Whisper (product). One accent carries action and live state; risk severity owns four separate roles.

---

## Color system (OKLCH + hex)

### Surfaces

| Token | OKLCH | Hex |
|---|---|---|
| `--bg` | `oklch(0.155 0.008 146)` | `#0a0d0a` |
| `--surface-1` | `oklch(0.196 0.010 146)` | `#121612` |
| `--surface-2` | `oklch(0.228 0.012 146)` | `#191e19` |
| `--surface-3` | `oklch(0.268 0.014 146)` | `#222822` |
| `--line` | `oklch(0.302 0.012 146)` | `#2b302b` |
| `--line-strong` | `oklch(0.392 0.016 146)` | `#404840` |

### Ink

| Token | OKLCH | Hex | Role |
|---|---|---|---|
| `--ink` | `oklch(0.945 0.006 146)` | `#eaeeea` | primary text |
| `--ink-mid` | `oklch(0.875 0.010 146)` | `#d2d8d2` | headings, controls |
| `--ink-dim` | `oklch(0.835 0.011 146)` | `#c5cbc5` | secondary text |
| `--ink-faint` | `oklch(0.770 0.011 146)` | `#b0b6b0` | metadata (12px floor) |

### Accent

| Token | OKLCH | Hex | Role |
|---|---|---|---|
| `--accent` | `oklch(0.862 0.190 128)` | `#ade84f` | live/verified state, primary action, focus, links |
| `--accent-strong` | `oklch(0.790 0.200 128)` | `#95d11c` | accent hover |
| `--accent-ink` | `oklch(0.160 0.020 128)` | `#0b0f06` | text on accent |
| `--accent-wash` | `oklch(0.862 0.190 128 / 0.12)` | — | selected / live tint |
| `--accent-line` | `oklch(0.862 0.190 128 / 0.40)` | — | accent borders |

### Severity (state, not decoration)

| Token | OKLCH | Hex | Meaning |
|---|---|---|---|
| `--sev-critical` | `oklch(0.850 0.175 24)` | `#ff9b95` | CRITICAL |
| `--sev-high` | `oklch(0.840 0.150 62)` | `#ffb259` | HIGH |
| `--sev-moderate` | `oklch(0.880 0.120 96)` | `#efd777` | MODERATE |
| `--sev-low` | `oklch(0.785 0.020 146)` | `#b1bdb1` | LOW |

Severity is never carried by color alone: every chip also carries the level word and the score number.

**Contrast:** every text pair was checked with the design skill's `check.mjs`; the console reports **0** contrast/APCA findings. Light-on-dark compensation: body line-height 1.55, metadata floor 12 px, tabular numerals for all data.

---

## Typography

**Families**
- UI: `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Data: `ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace`

**Scale — ratio 1.3**

| Token | rem | px | Use |
|---|---|---|---|
| `--fs-2xs` | 0.6875 | 11 | labels, chips, metadata |
| `--fs-xs` | 0.75 | 12 | secondary rows, captions |
| `--fs-sm` | 0.8125 | 13 | body/short copy, panel titles |
| `--fs-md` | 0.9375 | 15 | base body, card city |
| `--fs-lg` | 1.21875 | 19.5 | top-alert title, metric value |
| `--fs-xl` | 1.585 | 25.4 | page title, card score |
| `--fs-2xl` | 2.0625 | 33 | reserved |

- Line-height: `--lh-tight` 1.15 (headings), `--lh-body` 1.55 (copy).
- Measure: the masthead description caps at `66ch`.
- Sentence case throughout; no uppercase eyebrow labels. Monospace is reserved for machine data.
- Metadata never drops below 12 px; controls are 44 px tall.

---

## Spacing — 1-4-9 rhythm

Base unit 4 px. Named steps: `--s1:4`, `--s2:8`, `--s3:12`, `--s4:16`, `--s5:24`, `--s6:36`, `--s7:48`, `--s8:64`.
Layout uses `gap`, not margins. Component padding uses `--s3`/`--s4`; section breaks use `--s6`.

---

## Radius — by role, not one global value

| Token | Value | Role |
|---|---|---|
| `--r-control` | 6px | buttons, chips, inputs, tags |
| `--r-surface` | 10px | panels, alert band, status rail |
| `--r-pill` | 999px | **status badge only** |
| dots / rails | 50% / 2–5px | indicators, bars, slider |

---

## Component tokens

- **Panels:** `--surface-1` background, 1px `--line` border, `--r-surface`; internal rows separated by `--line`, never nested cards.
- **Risk row:** flat, `--surface-1`; hover `--surface-2`; severity via labelled chip + score color; disclosure is a native button.
- **Feed row:** flat; family tag + time + headline + meta.
- **Instrument strip:** one bordered surface divided by `--line`, five readings, first reading widest.
- **Priority band:** top-alert (accent top border) + status rail; stacks below 820px.
- **Focus ring:** `2px solid var(--accent)`, offset 2px (input 1px). Never removed.

## Button system

| Variant | Spec |
|---|---|
| Primary | `--accent` bg, `--accent-ink` text, 700, 44px min-height, hover `--accent-strong` |
| Secondary / filter | transparent, `--line` border, `--ink-dim`; hover `--surface-2`; active `--accent` bg |
| Ghost | transparent, `--accent-line` border, `--accent` text |
| Disabled | opacity .5, `cursor:not-allowed`; loading uses "Settling…" and `aria-busy`-equivalent disabled state |

One verb per button: "Buy assessment", "Retry fetch", "Retry settlement", "Reset filters", "Jump to card", "Show details".

## Motion

- Durations: 150–280 ms for state, 0.8 s spin, 70 s marquee.
- Easing: linear for loops, ease for state.
- **Only `transform` and `opacity` animate.** No transitions on color/layout. Detail reveal is a display toggle, not a height animation.
- `prefers-reduced-motion: reduce` disables all animation and transitions, including the marquee and spinner.

---

## Anti-references

This surface must not look like:
- a cyan-on-navy SaaS dashboard;
- an indigo/purple AI gradient page;
- a grid of equal metric tiles;
- nested rounded cards with left accent rails;
- pill-shaped controls everywhere;
- a "hacker terminal" costume that uses monospace for prose.
