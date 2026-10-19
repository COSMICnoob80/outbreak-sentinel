---
id: 004
title: Backend news sources + sparkline plumbing
stage: general
date: 2026-10-19
surface: agent
model: z-ai/glm-5.3-flash
feature: outbreak-sentinel
branch: main
user: cosmicnoob (delegate task via soldier loop)
command: Attach authentic news sources, AI summary, sparkline + illustration data to every risk card on /risk and /telegraph/risk (soldier task 1 of the dashboard-v2 loop)
labels: [api, risk-card, sources, sparkline, llm-fusion, phr]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - outbreak-sentinel/app.py (RiskCard optional fields, _norm_card passthrough + helpers, both endpoints)
  - outbreak-sentinel/outbreak_sentinel.py (fusion prompt asks LLM for per-card summary)
tests:
  - pytest tests -q → 3 passed
  - live GET /risk → engine=llm, 5 cards, all 4 new fields populated from real Google News + open-meteo data
  - live POST /telegraph/risk (city=Karachi) → engine=llm, risk_card carries sources/summary/chart/illustration_hint
---

## Prompt

Attach authentic news sources + AI summary + sparkline/illustration data to every risk card in Outbreak Sentinel's API (/risk, /telegraph/risk). Rules: smallest viable diff; backwards-compatible additive fields; never invent fake data — only real items from collect_signals; never leak .env values.

## Response snapshot

Plumbed 4 optional fields (`sources [{title,url}]`, `summary`, `chart [{label,value}]`, `illustration_hint`) through the backend: RiskCard model gained optional fields; `_norm_card` passes through LLM extras; the fuse_with_groq prompt now asks for a per-card `summary` derived only from provided signals; new helpers `_pick_sources` (city→disease matching over real RSS items, dedupe, cap 5), `_sparkline` (7-day open-meteo precipitation), `_illustration_hint` (disease-cue-level string); `_attach_card_extras` stamps all four before both endpoints return. Rule-based fallbacks summarize from real drivers only. Live-verified on localhost: engine=llm, Karachi card carried a real Google News dengue-fatality source URL, LLM summary, 7-point precipitation sparkline, hint "dengue-heat-high".

## Outcome

- ✅ Impact: every card from both /risk and /telegraph/risk now ships sourcing + narrative + spark data; contract is additive only (old clients unaffected).
- 🧪 Tests: pytest 3 passed; live endpoint smoke on /risk and /telegraph/risk with all fields populated.
- 📁 Files: app.py, outbreak_sentinel.py (2-line prompt addition).
- 🔁 Next prompts: dashboard rendering of the 4 fields (soldier 0's UX task); chart still flat 0.0 rain days — consider news-count sparkline alternative.
- 🧠 Reflection: no code should ever synthesize sources or summaries — city/disease substring matching over real RSS titles kept "authentic only" without inventing data, and empty lists are the honest fallback for unmatched cities.
