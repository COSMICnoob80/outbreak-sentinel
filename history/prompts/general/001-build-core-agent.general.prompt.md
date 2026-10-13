---
ID: 1
TITLE: Build core Outbreak Sentinel agent
STAGE: general
DATE_ISO: 2026-10-11
SURFACE: agent
MODEL: meituan/longcat-2.5-preview:free
FEATURE: none
BRANCH: main
USER: cosmicnoob
COMMAND: build outbreak_sentinel.py
LABELS: [python, agent, bio-surveillance, groq, weather, news]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - outbreak_sentinel.py
  - config.yaml
  - requirements.txt
  - README.md
  - .env.example
TESTS_YAML:
  - python3 outbreak_sentinel.py --dry-run (verified: outputs risk cards for 5 cities)
PROMPT_TEXT: |
  Build the core Outbreak Sentinel agent. Read the existing README.md blueprint first. Create a Python agent that: (1) fetches news search results for outbreak-related keywords, (2) fetches weather data for major Pakistani cities, (3) uses a Groq LLM to fuse the signals into an outbreak risk card, (4) outputs the risk card with risk level, drivers, and confidence. The agent should be runnable as a standalone script. Create: outbreak_sentinel.py (main agent), config.yaml (config), requirements.txt (dependencies), and a README.md update with run instructions. Keep it minimal but functional. Do NOT create a full web UI — just the core agent that outputs to console.
RESPONSE_TEXT: |
  Built and verified the core Outbreak Sentinel agent. Created outbreak_sentinel.py (async Python agent with news/weather/social fetching, Groq LLM fusion, rule-based fallback, color-coded console output), config.yaml (5 Pakistani cities, 5 diseases, keywords, thresholds), requirements.txt (aiohttp, feedparser, pyyaml, groq), .env.example, and updated README.md with run instructions. Verified with --dry-run: successfully fetched 13 news articles, 25 social posts, 5 city weather forecasts, and output risk cards (Karachi HIGH, others MODERATE).
OUTCOME: success
EVALUATION: Agent runs standalone, fetches real data, outputs formatted risk cards. Groq fusion requires API key; rule-based fallback works without.
