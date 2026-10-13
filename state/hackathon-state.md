# Hackathon State — OUTBREAK SENTINEL

**Single source of truth for deadlines, targets, and track selection.**
Director persona updates this; SPINE.md links here.

- Updated: 2026-10-13
- Primary: **Telegraph Season II — AWS CDS Agentic AI Partner** (lablab.ai, Sep 14–Oct 28, $40K)
- Deadline: **2026-10-28** (both Telegraph Season II and the AWS Agentic AI track share this date)
- Fallback: CodeTheCure (Devpost, Oct 10–28)
- Track rationale: the moat is agentic orchestration — the studio-team pattern itself is the demo, not the health domain.

## Build State (2026-10-13)
- Core agent runs end-to-end (rule-based fallback; Groq 404s on configured model `rule-based`, key present)
- Receipt engine live: publish.py persists HIGH/CRITICAL cards; verify.py resolves them; API exposes /receipts, /receipts/{id}, /scoreboard
- 1 receipt verified (rcpt-9575593f78c6, CONFIRMED)
