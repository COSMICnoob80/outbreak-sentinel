# Hackathon State — OUTBREAK SENTINEL

**Single source of truth for deadlines, targets, and track selection.**
Director persona updates this; SPINE.md links here.

- Updated: 2026-10-15
- Primary: **Telegraph Season II — AWS CDS Agentic AI Partner** (lablab.ai, Sep 14–Oct 28, $40K)
- Deadline: **2026-10-28** (both Telegraph Season II and the AWS Agentic AI track share this date)
- Fallback: CodeTheCure (Devpost, Oct 10–28)
- Track rationale: the moat is agentic orchestration — the studio-team pattern itself is the demo, not the health domain.

## Build State (2026-10-15)
- `.env` now loads via stdlib `load_env_file()` in `outbreak_sentinel.py` (no python-dotenv); Groq key resolves with no env preloaded
- `config.yaml` model fixed `"rule-based"` → `llama-3.3-70b-versatile`; but that model 404s on this key (`model_not_found`) — NOT available, so real LLM fusion is still unconfirmed
- Account exposes 11 models (gpt-oss-120b/20b, qwen3.8-27b, allam-2-7b, …); `llama-3.3-70b-versatile` absent → **operator must pick the fusion model**
- Receipt ledger honest: fabricated future-dated resolve purged; 1 receipt, status OPEN, 0 resolved; 3 tests pass
- Receipt engine live: publish.py persists HIGH/CRITICAL cards; verify.py resolves them; API exposes /receipts, /receipts/{id}, /scoreboard
