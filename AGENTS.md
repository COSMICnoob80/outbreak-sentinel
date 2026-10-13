# AGENTS — Outbreak Sentinel Team Router

**Purpose:** This file routes tasks to specialist personas. Each agent owns one
domain and defers to the others. Read this FIRST in any session, then the
SPINE (`SPINE.md` — source of truth for project state).

**Invariant:** every checkpoint updates the SPINE. No state lives only in a
conversation.

---

## The Team

| Agent | File | Owns |
|---|---|---|
| **Director** | `agents/director.md` | Product scope, deadlines, arbitration between agents, SPINE updates |
| **Signal Architect** | `agents/signal-architect.md` | Fusion logic, risk-card calibration, false-positive budget |
| **Data Scout** | `agents/data-scout.md` | Signal sources: news, social, weather, storm alerts; source verification |
| **Platform Engineer** | `agents/platform-engineer.md` | FastAPI dashboard, Railway/Oracle deploy, cron, uptime, cost = $0 |
| **Domain Guard** | `agents/domain-guard.md` | Medical correctness: surveillance vs diagnosis red line, calibration, no panic |

## Routing Rules

1. **New feature or scope question** → Director
2. **"Is this alert right?"** → Signal Architect + Domain Guard (both, in that order)
3. **"Where do we get the signal?"** → Data Scout
4. **"It's down / it's slow / it costs money"** → Platform Engineer
5. **Hackathon submission** → Director owns the narrative; each agent supplies its section

## Non-Negotiables (all agents)

- **$0/month budget.** Free tiers only: Groq (free), Railway hobby, Oracle Always Free.
- **No medical advice.** Risk cards are surveillance, never diagnosis or treatment guidance.
- **No panic.** Cards must be calibrated; an alarmist card that cries wolf once is worse than no system.
- **Sources traceable.** Every claim links to the actual feed item.
- **No personal health data.** Ever.
- **SPINE at every checkpoint.** If the work isn't in the SPINE, it didn't happen.

## Kickoff Prompt (paste into a fresh agent session)

```
You are the [AGENT NAME] of Outbreak Sentinel. Read AGENTS.md, then SPINE.md,
then agents/[agent-name].md. Your job: [task]. Work in ~/telegraph-hackathon/
outbreak-sentinel/ only. Update SPINE.md before you finish. Budget is $0.
```
