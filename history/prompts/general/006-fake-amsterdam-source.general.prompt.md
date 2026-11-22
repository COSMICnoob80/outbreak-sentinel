---
ID: 006
TITLE: Fake Amsterdam source and cloud deploy path
STAGE: general
DATE: 2026-11-17
SURFACE: agent
MODEL: z-ai/glm-5.3-flash
FEATURE: outbreak-sentinel
BRANCH: main
USER: COSMICnoob80
COMMAND: normal chat
LABELS: [credibility, citations, llm-provider, render]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - outbreak_sentinel.py (provider chain, 7-day city window)
  - app.py (evidence_line, /intel/llm)
  - dashboard/index.html (source rendering)
  - config.yaml (city_lookback_hours)
  - tests/test_citations.py (new)
  - .env (CMDC_API_KEY, LLM_MODEL — values not recorded)
TESTS_YAML:
  - pytest -q → 24 passed
  - GET /intel/llm → provider commandcode, ok true, 1686 ms
  - GET /risk?city=Karachi → engine llm, HIGH 0.8, 2 Express Tribune sources
  - GET /risk?city=Amsterdam → LOW 0.4, 0 sources, 0 city-specific reports
  - GET /risk (all cities) → 10 cards in 25.6 s
---

## PROMPT_TEXT

User attached three screenshots: (1) Google AI Overview stating Amsterdam has no local
dengue transmission and no established Aedes vectors in the Netherlands, (2) a dashboard
news card reading "Dengue death toll crosses 500 as 3 more die - Aijker Patrika" tagged
to Amsterdam with "value est. 72 · conf 0.91", (3) the Render "Create a new Service"
screen. Message:

> WTH man??? ss attached, highly doubtful and credibility at stake as per my fears that
> are now valid. Also render has been signed in via github, now what next??????

## RESPONSE_TEXT

- Identified the Amsterdam card as a Bangladesh story (Ajker Patrika is a Dhaka outlet)
  wrongly attached to Amsterdam; the partial fix (commit 09864a3) already removed it —
  verified live: Amsterdam now LOW, 0 sources, evidence line "0 city-specific reports in
  the last 7 days".
- Found the LLM path dead: Groq returns HTTP 403 for the stored key. Rewired fusion to
  the Command Code provider (model z-ai/glm-5.3-flash); verified /intel/llm ok in 1686 ms.
- Widened city news to 7 days so real reporting surfaces: Karachi now HIGH 0.8 with two
  Express Tribune citations; Lahore MODERATE 0.7; Islamabad MODERATE 0.6.
- Opened Soldier O for the remaining credibility defects: topic-matched sources (a
  Karachi robbery story was cited as dengue evidence), truthful signal kinds (an
  editorial was labelled WEATHER), and a 5-minute grid cache (26 s → instant repeat).
- Render: gave the exact Web Service fields and flagged the free-tier sleep behaviour.

OUTCOME: credibility defects identified with live evidence; two fixed and verified, the
rest in flight under Soldier O.
