# Outbreak Sentinel 🛰️ — Bio-surveillance Early Warning (PARKED BLUEPRINT)

> **Status: PARKED** — second Track 3 concept for the Telegraph Hackathon ecosystem.
> Primary entry is [RxTruth](https://github.com/COSMICnoob80/rxtruth). This blueprint is preserved
> so the idea survives beyond the hackathon — it deserves a full build when the right time comes.

## The Idea

An autonomous bio-surveillance agent that fuses multiple Telegraph intelligence intents to detect
early outbreak signals **before official health systems announce them**:

```
NEWS_SEARCH ──────┐
TWITTER_SEARCH ───┤
SENTIMENT_ANALYSIS ┼──→ signal fusion (cluster detection) ──→ OUTBREAK RISK CARD
WEATHER_FORECAST ──┤        (Groq LLM subnet 102)            ⚠ Dengue, Karachi — HIGH
STORM_ALERT ───────┘                                        drivers: 340% news uptick +
                                                            monsoon rain + panic score 0.81
```

**Why it matters**: dengue/malaria/cholera outbreaks leave digital exhaust (news spikes, social
panic, weather triggers) days before ministries confirm. An MBBS-built radar that catches those
signals is a genuine public-health tool — and a killer demo.

## Telegraph Intents Used

| Intent | Role |
|---|---|
| `NEWS_SEARCH` | Global/local outbreak news sweep (DeSearch subnet 101) |
| `TWITTER_SEARCH` | Social chatter on symptoms/cluster keywords |
| `SENTIMENT_ANALYSIS` | Panic/fear scoring on chatter |
| `WEATHER_FORECAST` | Environmental triggers (rain, flooding, temperature) |
| `STORM_ALERT` | Extreme-weather events that precede outbreaks |
| `CHAT_COMPLETION` | Signal fusion + risk verdict (Groq subnet 102) |

6 intents fused = strong multi-intent scoring story (same as RxTruth).

## Architecture (when built)

- TypeScript + Express + tsx (same stack as RxTruth — reuse the x402 payment layer)
- Rolling 24h window per region; cluster detection = keyword frequency + sentiment + weather overlap
- SQLite timeline per region; risk cards as SVG (RxTruth's `cards.ts` pattern)
- Optional X auto-alerts: `⚠ OUTBREAK RISK: Dengue — Karachi — HIGH · drivers: …`

## Why Parked

1. **RxTruth is the stronger hackathon entry** — doctor-vs-misinformation is a cleaner story,
   and its pipeline is already built and compiling.
2. Outbreak signals are **rare in a 7-day judging window** — the demo can look dead even when
   the system works. RxTruth produces fresh verdicts every run.
3. Both ideas share ~70% of their plumbing — building RxTruth first means Sentinel is a
   config + fusion-logic change later.

## Build Order When Resumed

1. Fork RxTruth's `payments/`, `clients/`, `store.ts`, `cards.ts` as-is
2. Replace pipeline: harvest → **cluster detection** → risk verdict → alert card
3. Add region config (start: Karachi dengue season, monsoon belt)
4. Demo mode: replay historical outbreak (e.g. 2024 dengue spike) to prove the detector fires

## License

MIT — same as RxTruth.
