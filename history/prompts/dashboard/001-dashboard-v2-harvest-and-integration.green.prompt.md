---
id: 001
title: "Dashboard v2 harvest and integration"
stage: green
date_iso: 2026-10-19
surface: agent
model: z-ai/glm-5.3-flash
feature: dashboard
branch: main
user: cosmicnoob
command: subagent task — harvest viral UI patterns, write state/dashboard-v2-design-spec.md, implement dashboard/index.html v2
labels: ["dashboard","feature-harvesting","pwa","ui-redesign"]
links:
  spec: "state/dashboard-v2-design-spec.md"
  ticket: null
  adr: null
  pr: null
files:
  - dashboard/index.html
  - state/dashboard-v2-design-spec.md
tests:
  - node --check on extracted <script> (pass)
  - node smoke tests: v1-only / all-fields / empty-card degrade renders (pass)
  - sparkline geometry + citation chips construction verified (pass)
  - git diff dashboard/manifest.json service-worker.js vs HEAD (empty — unchanged)
---

## PROMPT_TEXT

Dashboard feature harvesting + design upgrade for the Outbreak Sentinel dashboard
(dashboard/index.html). Research viral reverse-engineered UI repos on GitHub; extract
concrete stealable features (layout rhythms, card anatomy, data-viz patterns, color
systems, hero/summary blocks, empty/loading states, micro-interactions). Write feature-spec
to state/dashboard-v2-design-spec.md. Implement the refined dashboard in dashboard/index.html
(vanilla CSS/JS only, keep manifest.json and service-worker.js intact). New card anatomy must
render 4 new optional fields if present in /risk responses: sources ({title,url} list),
summary (string), chart ({label,value} list) as sparkline, illustration_hint (string).
All fields optional — card degrades gracefully when absent. Verify JS syntax (node --check),
manifest/SW unchanged. Commit and push with feat(dashboard): v2 message.

## RESPONSE_TEXT

Harvested via HTML/JS + published token specs channel (Hermes popular-web-designs skill —
Linear.app reverse-engineered design-system doc — plus dashboard pattern guides):
FR-01 luminance-stacked surfaces (rgba-white card layers, whisper borders), FR-02 Inter/
JetBrains Mono typography rhythm, FR-03 metric strip (auto-fill minmax grid), FR-04
skeleton-shimmer loading that predicts final card shape, FR-05 three-state doctrine
(loading/empty+CTA/error with retry replacing alert), FR-06 card anatomy with citation
chips + AI summary + pure-SVG sparkline + illustration_hint strip (all 4 optional,
graceful degrade verified by smoke tests), FR-07 micro-interactions (hover luminance
step, focus rings, HIGH/CRITICAL chip pulse), FR-08 8px spacing rhythm. Implemented
wholly in dashboard/index.html; manifest.json and service-worker.js untouched (diff
verified empty). Committed feat(dashboard): v2 design and pushed to origin/main.
