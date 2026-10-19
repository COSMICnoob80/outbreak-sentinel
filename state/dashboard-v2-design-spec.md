# Dashboard v2 — Harvested Viral UI Pattern Spec

**Feature:** outbreak-sentinel dashboard/about → `dashboard/index.html` (vanilla HTML/CSS/JS PWA)
**Owner surface:** FastAPI `/telegraph/status` + `/telegraph/risk` (app.py, untouched)
**Channel of harvest:** Published design systems via reverse-engineered token specs (Hermes `popular-web-designs` skill — Linear.app reverse-engineered design system doc) + dashboard UI pattern guides (skeleton-shimmer, three-state doctrine). Channel = published spec, not REA decompilation; the reference apps are website-analyzable and their design tokens are freely published.
**Contract kept:** manifest.json and service-worker.js unchanged; PWA shell caching intact; all data still fetched from `/telegraph/*`.

---

## What was harvested (features, with evidence)

### FR-01 — Luminance-stacking dark surfaces (Linear)
- Steal: near-black canvas `#08090a`, panel `#0f1011`, elevated cards as **translucent white overlays** (`rgba(255,255,255,0.02→0.05)`) instead of solid hex backgrounds; elevation is expressed by background-opacity steps, never drop shadows.
- Borders are semi-transparent white `rgba(255,255,255,0.05)` (subtle) / `rgba(255,255,255,0.08)` (standard).
- Single chromatic accent only for interactive/CTA elements (brand indigo `#5e6ad2` / hover `#828fff`); keep risk-semantics colors (green/amber/red) reserved for status dots and level chips.
- Evidence: Linear.app.md §2, §6, §7 (reverse-engineered token spec).

### FR-02 — Typography rhythm & hierarchy (Linear)
- Inter (Google Fonts CDN, `system-ui` fallback — degrades offline) with negative letter-tracking at display sizes; three weight tiers 400/510(use 500)/590(use 600); mono (JetBrains Mono → ui-monospace fallback) for hashes, tx ids, amounts.
- H1 compresses at ~32px with `-0.5px..-1px` tracking; labels are 10–11px uppercase, letter-spaced micro-labels.
- Evidence: Linear.app.md §2–§3.

### FR-03 — Hero/summary block ("metric strip", Stripe/Vercel dashboard pattern)
- One large primary number (risk score) + one comparison line + one micro-visual, at 28–32px, in a grid row `auto-fill, minmax(200px,1fr)` for the settlement/status stats.
- Evidence: dashboards pattern guide "How Should You Structure the Metric Strip" — one primary number, one comparison, one visual.

### FR-04 — Skeleton loading states with shimmer (Stripe/Linear/Notion)
- While `/telegraph/risk` runs: card-shaped skeletons that **predict final layout shape** (rows where rows will be), animated shimmer via CSS `background-position` gradient sweep (2–4s loop).
- Skeleton mirrors card anatomy; no layout jump when content resolves.
- `prefers-reduced-motion` media query disables shimmer.
- Evidence: Shimmer UI pattern docs; "The Loading State Is the Product" — *the loading shape predicts the final shape*.

### FR-05 — Three-state doctrine (loading / empty / error with retry)
- Every async surface has exactly three distinguishable states: skeleton (loading), an empty state (one sentence + CTA — "Run your first paid assessment to generate an intelligence card"), and an error banner with retry (not an `alert()`).
- Evidence: dashboard patterns 2026 guide; UIGuides loading-state guide.

### FR-06 — Card anatomy with source attribution (Perplexity-style cited intelligence)
- Risk card renders optional `sources` as citation chips: `[n] title` linking to `url`, rel-safe, external.
- Optional `summary` renders as a conversational "what this means" block above the technical drivers.
- Optional `chart` (`[{label,value}]`) renders as an inline **SVG sparkline** (no chart library): polyline stroke in accent color, gradient area fill, label/value in mono footer tooltips row.
- Optional `illustration_hint` strings drive a zero-dependency thematic visual (glyph + hint caption strip) on the card header.
- **All four are optional and degrade to the current v1 card silently when absent.** Guard clauses only; never `undefined` text on screen.
- Evidence: citation-chip pattern (Perplexity/You.com answered-by semantics), sparkline-in-card pattern from FR-03 metric strip.

### FR-07 — Micro-interactions (Linear/Stripe)
- Card hover: background opacity step up + border brighten; transform lift ≤2px, 120–160ms ease.
- Buttons: primary CTA filled accent; loading state swaps label ("Running…" → button-level state) and disables with reduced-opacity, not spinner emoji.
- Focus-visible rings on inputs/links (accessibility).
- Level chips (CRITICAL/HIGH/MODERATE/LOW/INFORMATIONAL/MINIMAL) fire a subtle pulse animation on first paint of a HIGH+ card, disabled under reduced-motion.
- Evidence: Linear.app.md §4 buttons/cards; standard micro-interaction folklore in the harvested repos.

### FR-08 — Distribution rhythm / spacing grid
- Base 8px spacing grid; card padding 16–20px; sections separated by 24px+; max content width ~1100px.
- Evidence: Linear.app.md §5 (8px base, luminance-as-whitespace).

---

## Card anatomy (v2) — contract

```
┌──────────────────────────────────────────────┐
│ [illustration Hint visual]  CITY · DISEASE   │  header row (optional hint)
│ RISK_LEVEL chip  ·  confidence               │  status row
│                                              │
│ "summary ..."            ← only if summary   │  AI summary block
│ Sparkline (chart[])      ← only if chart     │  inline SVG
│ drivers: a; b; c                              │  technical drivers
│ [1] source title ↗ [2] source title ↗        │  citation chips (sources[])
└──────────────────────────────────────────────┘
```

## Acceptance criteria

- [x] Card renders unchanged when none of the 4 new fields present (pixel-compatible behavior with v1 content set)
- [x] Each field renders independently when alone (`summary` w/o `chart`, etc.)
- [x] `sources` chips are real `<a target="_blank" rel="noopener noreferrer">`
- [x] Sparkline is pure SVG built via DOM/JS, no dependency, negative values clamped
- [x] Skeleton shimmer shows during fetch; result resolves into real shape
- [x] Error path shows banner with retry, no alert()
- [x] `node --check` passes on extracted script
- [x] manifest.json + service-worker.js byte-identical to pre-change
- [x] SW registration + offline banner kept

## Out of scope

- Any backend/app.py change; new endpoints; chart library; theming toggle; extra verticals; SW cache-busting.
