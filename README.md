# Outbreak Sentinel 🛰️ — Bio-surveillance Early Warning

> **Status: BUILT** — Core agent functional. Fuses news, weather, and social signals into outbreak risk cards.

## What It Does

An autonomous bio-surveillance agent that fuses multiple intelligence signals to detect
early outbreak signals **before official health systems announce them**:

```
NEWS_SEARCH ──────┐
WEATHER_FORECAST ─┼──→ signal fusion (Groq LLM) ──→ OUTBREAK RISK CARD
SOCIAL_CHATTER ───┘                                ⚠ Dengue, Karachi — HIGH
                                                   drivers: news uptick +
                                                   monsoon rain + panic score
```

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
- Groq model selection

### 3. Set API Key (Optional but Recommended)

```bash
cp .env.example .env
# Edit .env and add your Groq API key
export GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com)

### 4. Run

```bash
# Full mode (with Groq LLM fusion)
python outbreak_sentinel.py

# Dry run (rule-based scoring only, no API key needed)
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

## Output

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

## Architecture

```
outbreak_sentinel.py    — Main agent (async, standalone)
config.yaml             — Cities, diseases, keywords, thresholds
requirements.txt        — Python dependencies
.env.example            — API key template
```

### Signal Sources

| Signal | Source | Method |
|--------|--------|--------|
| News | Google News RSS | Keyword search with time filter |
| Weather | Open-Meteo API | 7-day forecast per city |
| Social | Google News RSS | Keyword search (proxy for Twitter) |
| Sentiment | Local | Keyword-based panic scoring |
| Fusion | Groq LLM | Multi-signal reasoning |

### Risk Levels

- **CRITICAL** (≥70 score): Multiple strong signals aligned — immediate action recommended
- **HIGH** (≥50): Strong signals — investigate and prepare
- **MODERATE** (≥30): Some signals — continue monitoring
- **LOW** (<30): Baseline — routine surveillance

## Configuration

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
  news_high: 15        # More sensitive = lower number
  news_medium: 8
  sentiment_high: 0.5
  temp_high: 33.0
  rain_high: 40.0
```

## How It Works

1. **Fetch**: Async HTTP requests to Google News RSS and Open-Meteo
2. **Score**: Keyword-based sentiment analysis on headlines
3. **Fuse**: Groq LLM analyzes all signals per city and produces risk verdicts
4. **Fallback**: If Groq unavailable, rule-based scoring using configurable thresholds
5. **Output**: Color-coded risk cards with drivers and recommendations

## Limitations

- **News source**: Uses Google News RSS (no direct Twitter API access)
- **Sentiment**: Simple keyword-based scoring (not ML-based)
- **Weather**: 7-day forecast only (no historical analysis)
- **Geographic**: Pakistan-focused (easily extensible)

## Future Enhancements

- [ ] Direct Twitter/X API integration
- [ ] ML-based sentiment analysis
- [ ] Historical trend analysis
- [ ] SMS/email alerts
- [ ] Web dashboard
- [ ] More cities and diseases

## License

MIT
