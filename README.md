# Outbreak Sentinel 🛰️ — agentic early warning with a verifiable prediction ledger

> **We don't just alert. We issue a signed prediction and later prove whether we were right.**

Outbreak Sentinel is a **platform**, not a single-disease app. One deterministic
engine watches any signal set, scores it, emits a **calibrated risk card**, logs it
as a **tamper-evident receipt**, and later **resolves it against reality**. An LLM
never decides anything — it only narrates the card it is handed. The name reflects
our first vertical — disease surveillance — but the engine is vertical-agnostic.

```
open signals ─→ score (deterministic) ─→ narrate (LLM) ─→ calibrated risk card ─→ signed receipt ─→ resolve vs reality
news / weather / social
```

## Why it's different: the receipt ledger

Anybody can print a red alert. The rare thing is **keeping score**. Every
`HIGH`/`CRITICAL` call becomes a receipt:

- **Tamper-evident** — id is the sha256 of the card's content; the ledger is
  append-only (`history/receipts.jsonl`), with no rewrite or un-resolve path.
- **Resolvable** — a human later marks it `CONFIRMED` or `REFUTED` against a real
  source; resolution appends a *new* event, so history is never mutated.
- **Auditable** — `GET /scoreboard` is the honest track record: calls made,
  calls resolved, verdicts. `resolved: 0` means "not yet checked", not "hidden".

That turns "trust our AI" into "check our ledger" — the only thing that makes an
early warning worth acting on.

## Verticals — one engine, many domains

The engine never changes. A **vertical** is a ~50-line declarative config: what to
watch, which signals, how to read the weather, and *what `HIGH` means*. See
[`verticals/README.md`](verticals/README.md) for the recipe.

| Vertical | Watches | Signals | `HIGH` means |
|---|---|---|---|
| `bio-surveillance` | Cities, diseases | news + weather + social | outbreak likely within 7 days |
| `wildfire` | Fire-prone regions | news + weather (wind, humidity) | fast-spreading fire within 48h |
| `supply-chain` | Global trade hubs | news + weather + social | hub disruption within 7 days |

```python
from verticals import all_verticals
for v in all_verticals():
    print(v.describe())
```

Adding a vertical compiles to the same config the engine already reads
(`Vertical.to_config()`), so fusion, calibration, the ledger, and resolution all
come for free.

## Quick Start

### 1. Install Dependencies

```bash
cd ~/telegraph-hackathon/outbreak-sentinel
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml` to customize:
- Cities to monitor
- Diseases to track
- News/social keywords
- Risk thresholds
- LLM model id (`LLM_MODEL`, default `tencent/hy4-flash`)

### 3. Set API Key (Optional but Recommended)

```bash
cp .env.example .env
# Edit .env and add your Command Code provider key
CMDC_API_KEY=your_cmdc_api_key
```

The LLM provider is the **Command Code provider API** — OpenAI-compatible at
`https://api.commandcode.ai/provider/v1`, model `tencent/hy4-flash`, key read from
`CMDC_API_KEY`. Confirm it is live:

```bash
curl localhost:8000/intel/llm   # {"provider":"commandcode","ok":true}
```

`GROQ_API_KEY` is **optional**. It is only consulted as a fallback when a working
key is supplied; Groq currently returns HTTP 403 on our account, so it is not the
active engine.

### 4. Run

```bash
# Full mode — deterministic cards + LLM narration
python outbreak_sentinel.py

# Dry run (deterministic scoring only, no API key needed)
python outbreak_sentinel.py --dry-run

# Custom config
python outbreak_sentinel.py --config /path/to/config.yaml
```

### 5. Schedule with Cron

```bash
# Run every 6 hours
crontab -e
# Add:
0 */6 * * * cd ~/telegraph-hackathon/outbreak-sentinel && /usr/bin/python3 outbreak_sentinel.py >> sentinel.log 2>&1
```

### 6. Deploy

The documented path is the **Render blueprint** in [`render.yaml`](render.yaml) —
free plan, `/health` check, secrets marked `sync: false`. Full click-by-click
instructions: [`docs/DEPLOY-RENDER.md`](docs/DEPLOY-RENDER.md).

## Verticals in depth — worked example: bio-surveillance

The original (and still first) vertical: watch Pakistan cities for the digital
exhaust of a brewing outbreak — news upticks, panic chatter, and vector-friendly
weather — days before official confirmation. **Surveillance, never diagnosis.**

The agent prints a color-coded risk card to console:

```
╔══════════════════════════════════════════════════════════════╗
║           🛰️  OUTBREAK SENTINEL — RISK ASSESSMENT            ║
║                      2024-01-15 14:30 PKT                   ║
╚══════════════════════════════════════════════════════════════╝

Signals: 45 news | 23 social | 5 cities

🔴 KARACHI — DENGUE — CRITICAL
   Confidence: 87%
   Drivers:
     • News uptick: 32 articles in 24h
     • Heavy rain forecast: 78.5mm
     • High panic sentiment: 0.72
   Recommendation: Activate vector control, issue public advisory

🟡 LAHORE — DENGUE — MODERATE
   Confidence: 54%
   Drivers:
     • Moderate news: 8 articles in 24h
   Recommendation: Continue monitoring
```

### Signal Sources

| Signal | Source | Method |
|--------|--------|--------|
| News | Google News RSS | Keyword search with time filter |
| Weather | Open-Meteo API | 7-day forecast per city |
| Social | Google News RSS | Keyword search (proxy for Twitter) |
| Sentiment | Local | Keyword-based panic scoring |
| Cards | Deterministic engine | Builds every card — city, disease, sources, 0–100 score |
| Narration | Command Code provider | Writes `summary` + `recommendation` for a card it is handed; discarded if it names another city, disease or source |

### Risk Levels

- **CRITICAL** (≥70 score): Multiple strong signals aligned — immediate action recommended
- **HIGH** (≥50): Strong signals — investigate and prepare
- **MODERATE** (≥30): Some signals — continue monitoring
- **LOW** (<30): Baseline — routine surveillance

The score is 0–100, built from city-specific reports inside a 7-day window plus
rain, heat and concern. Reports only count when the item names **this** city and
matches the queried disease, and repeat coverage of one story counts once. With
**zero** city-specific reports the card is capped at `LOW` with confidence ≤ 0.55 —
an unwitnessed outbreak never gets a confident card. That is the false-positive
budget, enforced in code rather than in prose.

### Adding a City

```yaml
cities:
  - name: Multan
    lat: 30.1575
    lon: 71.5249
```

### Adding a Disease

```yaml
diseases:
  - dengue
  - malaria
  - cholera
  - typhoid
  - hepatitis
  - measles  # new
```

### Adjusting Thresholds

```yaml
thresholds:
  sentiment_high: 0.6   # 0-1 panic score
  sentiment_medium: 0.3
  temp_high: 35.0       # °C
  rain_high: 50.0       # mm
```

## How It Works

1. **Fetch**: Async HTTP requests to Google News RSS and Open-Meteo
2. **Score**: City-scoped evidence density (7-day window) + rain, heat and keyword panic
3. **Build**: The deterministic engine assembles every card — city, disease, sources, numeric score, level, confidence
4. **Narrate**: The LLM writes only `summary` and `recommendation` for the card it is handed. Its response is discarded if it names another city, disease or source. Engine label: `deterministic+narrator`
5. **Fallback**: Without a provider the card keeps deterministic template prose — the grid is identical either way
6. **Receipt**: `HIGH`/`CRITICAL` cards persist as sha256-hashed receipts
7. **Resolve**: `python verify.py <id> CONFIRMED|REFUTED "<source>"` scores them
8. **Output**: Color-coded risk cards with drivers and recommendations

## API

```
GET /                    service health
GET /health              uptime probe ({"status":"ok", ...})
GET /intel/llm           provider proof ({"provider":"commandcode","ok":true})
GET /risk                fresh fused risk cards (optional ?city=)
GET /receipts            the ledger (optional ?status=OPEN|RESOLVED)
GET /receipts/{id}       one tamper-evident receipt (404 if unknown)
GET /scoreboard          calls made · resolved · verdicts
GET /cities /diseases    configured subject axis
```

## Architecture

See [`pitch/ARCHITECTURE.md`](pitch/ARCHITECTURE.md) for the full diagram and the
two seams (vertical config + delivery adapter).

```
verticals/            the domain seam: base.py + 3 verticals + registry
outbreak_sentinel.py  the engine: fetch → score → card (provider-agnostic LLM helper)
receipts.py           append-only ledger: make_receipt / ReceiptStore
publish.py            HIGH/CRITICAL cards → receipts
verify.py             human resolver: CONFIRMED | REFUTED + source
app.py                FastAPI dashboard/API
render.yaml           Render blueprint: free plan, /health check, sync:false secrets
docs/DEPLOY-RENDER.md the deployment guide
agents/               the studio-team pattern (director, signal architect, ...)
pitch/                one-pager, architecture, demo script, hackathon fit
config.yaml           cities, diseases, keywords, thresholds (bio vertical)
```

## Pitch & demo

- [`pitch/ONE-PAGER.md`](pitch/ONE-PAGER.md) — the universal pitch (any track).
- [`pitch/DEMO-SCRIPT.md`](pitch/DEMO-SCRIPT.md) — a 3-minute judge demo.
- [`pitch/HACKATHON-FIT.md`](pitch/HACKATHON-FIT.md) — which tracks fit, and why.

## Limitations

- **News source**: Google News RSS (no direct Twitter/X API access)
- **Sentiment**: keyword-based scoring (not ML-based)
- **Weather**: 7-day forecast only (no historical analysis)
- **Locations**: shipped verticals are region-focused (extensible via `verticals/`)
- **Resolution**: human-in-the-loop by design — a receipt is only scored when a
  person checks it against a real source

## Future Enhancements

- [ ] Delivery adapters (SMS / WhatsApp / email) behind the channel seam
- [ ] More verticals (crop disease, financial stress, traffic)
- [ ] ML-based sentiment analysis
- [ ] Historical trend analysis
- [ ] Automated source-watcher to pre-fill resolutions

## License

MIT
