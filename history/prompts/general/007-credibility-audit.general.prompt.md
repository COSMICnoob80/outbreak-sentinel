---
ID: 007
TITLE: Credibility audit and deterministic engine repair
STAGE: general
DATE: 2026-11-17
SURFACE: agent
MODEL: z-ai/glm-5.3-flash
FEATURE: outbreak-sentinel
BRANCH: main
USER: COSMICnoob80
COMMAND: normal chat
LABELS: [credibility, determinism, scoring, deploy]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - outbreak_sentinel.py (deterministic cards, density scoring, news retry+cache)
  - app.py (narrator contract, evidence lines)
  - dashboard/index.html (API score, real 7-day chart, percent confidences, footnote)
  - config.yaml (topic vocabulary, score bands)
  - render.yaml (new)
  - docs/DEPLOY-RENDER.md (new)
  - tests/ (50 → 73 tests)
TESTS_YAML:
  - pytest -q → 73 passed
  - GET /risk?disease=dengue ×2 → identical cities/levels/sources, engine deterministic+narrator
  - Karachi risk_score 30 == rendered 30/100, 2 sources, evidence count 2
  - GET /intel/llm → provider commandcode, ok true
  - docker build + docker run → /health 200, dashboard 200
---

## PROMPT_TEXT

Follow-on work from the same session: the founder reported a fabricated Amsterdam source
("Dengue death toll crosses 500 - Ajker Patrika", a Dhaka outlet) and asked what to do
about Render. Successive verification passes then uncovered further fabrication:
invented diseases per card, a console-calculated score, a hardcoded 24h timeline, and a
flat wall of identical LOW cards.

## RESPONSE_TEXT

- Rebuilt the risk grid as deterministic code (cards, sources, scores) with the LLM
  demoted to a narrator whose output is discarded when it names another city, disease or
  source.
- Scoped news per city with a 7-day window, city + topic matching, retry and per-city
  cache; the Bangladesh story can no longer reach Amsterdam.
- Recalibrated scoring to 7-day report density: Karachi and Lahore MODERATE at 70% with
  two real Express Tribune sources each; zero-report cities stay LOW and say so.
- Removed every number the system did not have: the invented score fallback, the
  hardcoded 24h timeline array, and the stale "Groq free tier" footer claim.
- Added a two-secret Render blueprint plus a plain-English deploy guide, and proved the
  container builds and boots.

OUTCOME: 73 tests green; every displayed number traced to the API payload; deploy reduced
to Blueprint → connect repo → paste two secrets. Remaining blocker: the founder's Render
click.
