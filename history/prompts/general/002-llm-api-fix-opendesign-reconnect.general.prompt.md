---
id: 002
title: LLM API fix + OpenDesign reconnect
stage: general
date: 2026-10-17
surface: agent
model: poolside/laguna-s-2.1:free
feature: outbreak-sentinel
branch: main
user: cosmicnoob
command: Consolidated commander request — settle settlement/demo/video/pitch/opendesign via studio team in YOLO mode
labels: [opendesign, agentic-ai, mcp, api-fix, pwa, infrastructure]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/COSMICnoob80/outbreak-sentinel/commit/c1dabdc
files:
  - outbreak-sentinel/app.py
  - .hermes/config.yaml
  - outbreak-sentinel/history/prompts/general/002-llm-api-fix-opendesign-reconnect.general.prompt.md
tests:
  - verify_llm_api.py (GET /risk → engine: llm, 5 cities)
  - verify_llm_api.py (POST /telegraph/risk → engine: llm, mocked settlement + tx hash)
  - MCP handshake: initialize → open-design v0.2.0, tools/list → 22 tools (collect_brief, write_file, list_projects, etc.)
---

## Prompt

ALONGSIDE SETTLEMENT, DEMO VIDEO and PITCH KIT, HANDLE the opendesign reconnection too alongside all other remaining tasks using the STUDIO TEAM soldiers synergistically, as I said earlier you as the COMMANDER and your soldiers, both are YOLO (all permissions bypass so I need end results only). I still feel ambigiuos about what exactly are we building, PWA or a truly agentic product that is one of its kind. May I SEE THE ARTIFACT of what has been built so far, is it available across all platforms and devices? Is it user-friendly? Has everything been built what was it???? WHAT??????????? Ready for Y Combinator or is it tooooo flattering and too different from the reality???? WHAT DO THE SOLDIERS REPORT from the trenches????? WHAT PICTURE INTEL SIGNIT ELINT do you see AEWACS KITT CHIEF OF STAFF?

## Response snapshot

Critical gate closed: app.py now runs LLM fusion FIRST at /risk and /telegraph/risk with transparent `engine: "llm"` field in response. Verified by verify_llm_api.py — GET /risk returns 5 differentiated city cards (HIGH Ludhiana malaria 81%, MODERATE Karachi fog, LOW others), ENGINE: llm. POST /telegraph/risk returns engine: llm with mocked settlement + tx hash. OpenDesign daemon rebuilt: repo cloned to DURABLE ~/.hermes/tools/open-design (not scratch), all 20 workspace packages built via pnpm -r build, daemon listening on 127.0.0.1:7456 (health ok v0.25.1), config.yaml repointed (scratch→tools, 1 line change), MCP stdio handshake successful (initialize → open-design v0.2.0, tools/list → collect_brief).

## Outcome

- ✅ Impact: The single most dangerous gap — rule-based API endpoints masquerading as agentic — is closed and verified. /risk and /telegraph/risk now return real LLM output from openai/gpt-oss-120b. OpenDesign MCP reconnect durable and working.
- 🧪 Tests: verify_llm_api.py PASSED (engine: llm on both endpoints, real city cards). MCP handshake PASSED (initialize + tools/list).
- 📁 Files: app.py +70/-28 lines, config.yaml 1-line path fix, 20 workspace packages built.
- 🔁 Next prompts: wallet key injection for live settlement, deploy auth for Railway/Render/Fly, student-only hackathon filtering.
- 🧠 Reflection: Soldiers (Command Code / Code) repeatedly burned on the 24h scratch prune — infrastructure must be installed in ~/.hermes/tools, NEVER cache/scratch. Large monorepo builds take 5+ minutes (pnpm -r build across 20 packages).

## Evaluation notes (flywheel)

- Failure modes observed: git checkout . reverted patches mid-test; 30s tool timeout killed git clones; missing @open-design/sidecar-proto ESM module (chain of unbuilt workspace packages — fixed via pnpm -r build).
- Graders run and results (PASS/FAIL): LLM API test PASS; MCP handshake PASS; daemon health-check PASS.
- Prompt variant: consolidated commander-style bulk request.
- Next experiment: add systemd --user unit for the daemon so it starts on boot (currently only survives while process is alive).
