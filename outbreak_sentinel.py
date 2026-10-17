#!/usr/bin/env python3
"""
Outbreak Sentinel — Bio-surveillance Early Warning Agent

Fuses news search, weather forecasts, and social sentiment signals
into outbreak risk cards using a Groq LLM for signal fusion.

Usage:
    python outbreak_sentinel.py [--config config.yaml] [--dry-run]
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiohttp
import feedparser
import yaml


def load_env_file(path=None) -> None:
    """Minimal stdlib .env loader (no python-dotenv dependency).

    Parses KEY=VALUE lines, strips surrounding quotes, skips blank and
    #comment lines, and never overwrites an already-set os.environ var.
    """
    env_path = Path(path) if path else Path(__file__).resolve().with_name(".env")
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

# ── Optional Groq ──────────────────────────────────────────────────────
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# ── ANSI Colors ────────────────────────────────────────────────────────
class C:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# ── Config ─────────────────────────────────────────────────────────────


def default_config() -> dict:
    return {
        "cities": [
            {"name": "Karachi", "lat": 24.8607, "lon": 67.0011},
            {"name": "Lahore", "lat": 31.5204, "lon": 74.3587},
            {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479},
            {"name": "Peshawar", "lat": 34.0151, "lon": 71.5249},
            {"name": "Quetta", "lat": 30.1798, "lon": 66.9750},
        ],
        "diseases": ["dengue", "malaria", "cholera", "typhoid", "hepatitis"],
        "news_keywords": [
            "dengue outbreak", "malaria cases", "cholera", "typhoid",
            "hepatitis", "fever outbreak", "hospital patients",
        ],
        "social_keywords": [
            "dengue symptoms", "malaria symptoms", "fever", "sick",
            "hospital overflow", "patients",
        ],
        "thresholds": {
            "news_high": 10,
            "news_medium": 5,
            "sentiment_high": 0.6,
            "sentiment_medium": 0.3,
            "temp_high": 35.0,
            "rain_high": 50.0,
        },
        "groq": {
            "model": "openai/gpt-oss-120b",
            "api_key_env": "GROQ_API_KEY",
        },
        "lookback_hours": 24,
    }


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file, merging with defaults."""
    config_path = Path(path)
    if not config_path.exists():
        print(f"{C.YELLOW}⚠ Config not found at {path}, using defaults{C.RESET}")
        return default_config()
    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}
    defaults = default_config()
    for key, value in user_config.items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            defaults[key].update(value)
        else:
            defaults[key] = value
    return defaults


# ── Signal Fetchers ───────────────────────────────────────────────────


async def fetch_news(
    session: aiohttp.ClientSession, keyword: str, lookback_hours: int
) -> list[dict]:
    """Fetch news headlines via Google News RSS."""
    q = f"{keyword} pakistan when:{lookback_hours}h"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
        feed = feedparser.parse(text)
        return [
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            }
            for entry in feed.entries[:20]
        ]
    except Exception as e:
        print(f"{C.DIM}  ⚠ News fetch failed for '{keyword}': {e}{C.RESET}")
        return []


async def fetch_weather(
    session: aiohttp.ClientSession, city: dict, forecast_vars=None
) -> dict:
    """Fetch 7-day forecast from Open-Meteo.

    ``forecast_vars`` (from the loaded vertical's ``forecast_vars``) determines
    which daily variables are requested, so a wildfire vertical actually gets
    wind + humidity instead of only temp/precip/weathercode.
    """
    if not forecast_vars:
        forecast_vars = (
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weathercode",
        )
    forecast_vars = tuple(forecast_vars)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": ",".join(forecast_vars),
        "timezone": "Asia/Karachi",
        "forecast_days": 7,
    }
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return {"city": city["name"], "error": f"HTTP {resp.status}"}
            data = await resp.json()
        daily = data.get("daily", {})
        times = daily.get("time", [])
        forecast = []
        for i in range(len(times)):
            entry = {"date": times[i]}
            for var in forecast_vars:
                vals = daily.get(var, [None] * len(times))
                entry[var] = vals[i] if i < len(vals) else None
            # Backward-compat aliases consumed by the rule-based fallback.
            if "temperature_2m_max" in entry:
                entry["temp_max"] = entry["temperature_2m_max"]
            if "temperature_2m_min" in entry:
                entry["temp_min"] = entry["temperature_2m_min"]
            if "precipitation_sum" in entry:
                entry["precipitation"] = entry["precipitation_sum"]
            forecast.append(entry)
        return {"city": city["name"], "forecast": forecast}
    except Exception as e:
        return {"city": city["name"], "error": str(e)}


async def fetch_social_chatter(session: aiohttp.ClientSession, keyword: str) -> list[dict]:
    """Fetch social chatter via Google News RSS as proxy."""
    q = f"{keyword} pakistan when:24h"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
        feed = feedparser.parse(text)
        return [
            {"title": entry.get("title", ""), "link": entry.get("link", "")}
            for entry in feed.entries[:15]
        ]
    except Exception:
        return []


# ── Sentiment Analysis ────────────────────────────────────────────────

PANIC_WORDS = {
    "outbreak", "epidemic", "panic", "crisis", "emergency",
    "surge", "spike", "death", "died", "fatal", "deadly",
}
FEAR_WORDS = {
    "fear", "worried", "concern", "alarm", "warning",
    "alert", "danger", "threat", "scared", "horrific",
}
HOPE_WORDS = {
    "recover", "recovering", "discharge", "treatment",
    "vaccine", "prevention", "control", "contained", "stable",
}


def simple_sentiment(text: str) -> float:
    """Simple keyword-based sentiment scoring. Returns 0-1 panic score."""
    text_lower = text.lower()
    panic_count = sum(1 for w in PANIC_WORDS if w in text_lower)
    fear_count = sum(1 for w in FEAR_WORDS if w in text_lower)
    hope_count = sum(1 for w in HOPE_WORDS if w in text_lower)
    score = (panic_count * 2 + fear_count - hope_count * 0.5) / 10
    return max(0.0, min(1.0, score))


# ── Rule-Based Risk (Fallback) ────────────────────────────────────────


def rule_based_risk(
    news_count: int, weather: dict, sentiment: float, thresholds: dict
) -> dict:
    """Fallback risk scoring when Groq is unavailable."""
    score = 0
    drivers = []

    if news_count >= thresholds["news_high"]:
        score += 40
        drivers.append(f"News uptick: {news_count} articles in 24h")
    elif news_count >= thresholds["news_medium"]:
        score += 20
        drivers.append(f"Moderate news: {news_count} articles in 24h")

    forecast = weather.get("forecast", [])
    if forecast:
        max_rain = max((d.get("precipitation") or 0) for d in forecast)
        max_temp = max((d.get("temp_max") or 0) for d in forecast)
        if max_rain >= thresholds["rain_high"]:
            score += 20
            drivers.append(f"Heavy rain forecast: {max_rain:.1f}mm")
        if max_temp >= thresholds["temp_high"]:
            score += 15
            drivers.append(f"High temperature: {max_temp:.1f}°C")

    if sentiment >= thresholds["sentiment_high"]:
        score += 25
        drivers.append(f"High panic sentiment: {sentiment:.2f}")
    elif sentiment >= thresholds["sentiment_medium"]:
        score += 10
        drivers.append(f"Moderate concern: {sentiment:.2f}")

    if score >= 70:
        risk_level = "CRITICAL"
    elif score >= 50:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    confidence = min(0.95, 0.4 + score / 100)

    return {
        "risk_level": risk_level,
        "score": score,
        "confidence": round(confidence, 2),
        "drivers": drivers,
    }


# ── Groq Fusion ──────────────────────────────────────────────────────


def _extract_json(text: str) -> Any:
    """Extract JSON from LLM response text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


async def fuse_with_groq(
    news_data: list, weather_data: list, social_data: list, config: dict
) -> list[dict]:
    """Fuse signals using Groq LLM."""
    api_key = os.environ.get(config["groq"]["api_key_env"])
    if not api_key:
        print(
            f"{C.YELLOW}⚠ {config['groq']['api_key_env']} not set, using rule-based fallback{C.RESET}"
        )
        return []

    client = Groq(api_key=api_key)
    model = config["groq"]["model"]

    vertical = config.get("_vertical") or {}
    forecast_vars = vertical.get("forecast_vars") or [
        "temperature_2m_max",
        "precipitation_sum",
        "weathercode",
    ]

    news_summary = (
        "\n".join(f"- {a['title']}" for a in news_data[:15])
        or "No recent outbreak news."
    )
    weather_lines = []
    for w in weather_data:
        if "forecast" not in w:
            continue
        stats = []
        for var in forecast_vars:
            vals = [d.get(var) for d in w["forecast"] if d.get(var) is not None]
            if not vals:
                continue
            if isinstance(vals[0], bool):
                continue
            if isinstance(vals[0], (int, float)):
                stats.append(f"{var}={max(vals):.1f}")
            else:
                stats.append(f"{var}={vals[0]}")
        weather_lines.append(f"- {w['city']}: " + ", ".join(stats))
    weather_summary = "\n".join(weather_lines) or "No weather data."
    social_summary = (
        "\n".join(f"- {p['title']}" for p in social_data[:15])
        or "No social chatter."
    )

    fusion_role = vertical.get("fusion_role", "outbreak risk analyst")
    subject_label = vertical.get("subject_label", "disease")
    risk_model = vertical.get("risk_model") or {}
    escalation = risk_model.get("escalation_rule", "")

    prompt = f"""You are an {fusion_role}. Analyze these signals and produce risk cards.

NEWS SIGNALS:
{news_summary}

WEATHER SIGNALS:
{weather_summary}

SOCIAL CHATTER:
{social_summary}

For each city, output a JSON array of risk cards:
[
  {{
    "city": "CityName",
    "disease": "most likely {subject_label} from signals",
    "risk_level": "LOW|MODERATE|HIGH|CRITICAL",
    "confidence": 0.0-1.0,
    "drivers": ["driver1", "driver2"],
    "recommendation": "brief public health action"
  }}
]

Rules:
- {escalation or "Be conservative: only escalate if multiple signals align"}
- Consider the weather variables provided as relevant to the domain
- Consider news frequency: more articles = higher risk
- Consider sentiment: panic/fear words = higher risk

Output ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
        result_text = response.choices[0].message.content
        parsed = _extract_json(result_text)
        if parsed is None:
            print(f"{C.YELLOW}⚠ Could not parse Groq response as JSON{C.RESET}")
            return []
        if isinstance(parsed, dict):
            if "risk_cards" in parsed:
                return parsed["risk_cards"]
            return [parsed]
        return parsed
    except Exception as e:
        print(f"{C.YELLOW}⚠ Groq fusion failed: {e}{C.RESET}")
        return []


# ── Risk Card Output ──────────────────────────────────────────────────


def output_risk_card(
    risk_cards: list[dict],
    news_total: int,
    weather_count: int,
    social_total: int,
):
    """Pretty-print the risk card to console."""
    now = datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M PKT")

    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════════╗{C.RESET}")
    print(
        f"{C.BOLD}{C.CYAN}║           🛰️  OUTBREAK SENTINEL — RISK ASSESSMENT            ║{C.RESET}"
    )
    print(
        f"{C.BOLD}{C.CYAN}║                      {now}                        ║{C.RESET}"
    )
    print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════════╝{C.RESET}")

    print(
        f"\n{C.DIM}Signals: {news_total} news | {social_total} social | {weather_count} cities{C.RESET}\n"
    )

    if not risk_cards:
        print(f"{C.YELLOW}⚠ No risk cards generated (check API keys and network){C.RESET}")
        return

    for card in risk_cards:
        level = card.get("risk_level", "UNKNOWN")
        city = card.get("city", "Unknown")
        disease = card.get("disease", "Unknown")
        confidence = card.get("confidence", 0)
        drivers = card.get("drivers", [])
        recommendation = card.get("recommendation", "Monitor situation")

        if level == "CRITICAL":
            color = C.RED
            icon = "🔴"
        elif level == "HIGH":
            color = C.RED
            icon = "🟠"
        elif level == "MODERATE":
            color = C.YELLOW
            icon = "🟡"
        else:
            color = C.GREEN
            icon = "🟢"

        print(f"{color}{C.BOLD}{icon} {city.upper()} — {disease.upper()} — {level}{C.RESET}")
        print(f"   Confidence: {confidence:.0%}")
        if drivers:
            print(f"   Drivers:")
            for d in drivers:
                print(f"     • {d}")
        print(f"   Recommendation: {recommendation}")
        print()


# ── Main ─────────────────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser(
        description="Outbreak Sentinel — Bio-surveillance Early Warning"
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument(
        "--vertical", default=None,
        help="Vertical slug to run (e.g. wildfire); overrides --config",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without Groq (rule-based only)"
    )
    args = parser.parse_args()

    if args.vertical:
        from verticals import get_vertical

        defaults = default_config()
        vcfg = get_vertical(args.vertical).to_config()
        for key, value in vcfg.items():
            if isinstance(value, dict) and isinstance(defaults.get(key), dict):
                defaults[key].update(value)
            else:
                defaults[key] = value
        config = defaults
    else:
        config = load_config(args.config)

    print(f"{C.CYAN}🛰️  Outbreak Sentinel starting...{C.RESET}")
    print(f"   Monitoring {len(config['cities'])} cities, {len(config['diseases'])} diseases")
    print(f"   Lookback: {config['lookback_hours']}h")
    print()

    async with aiohttp.ClientSession() as session:
        # Fetch news
        print(f"{C.DIM}📰 Fetching news...{C.RESET}")
        news_results = await asyncio.gather(
            *[
                fetch_news(session, kw, config["lookback_hours"])
                for kw in config["news_keywords"]
            ]
        )

        # Fetch weather
        print(f"{C.DIM}🌤️  Fetching weather...{C.RESET}")
        _vertical = config.get("_vertical") or {}
        _forecast_vars = _vertical.get("forecast_vars") or None
        weather_results = await asyncio.gather(
            *[fetch_weather(session, city, _forecast_vars) for city in config["cities"]]
        )

        # Fetch social
        print(f"{C.DIM}💬 Fetching social chatter...{C.RESET}")
        social_results = await asyncio.gather(
            *[fetch_social_chatter(session, kw) for kw in config["social_keywords"]]
        )

    # Flatten
    all_news = [a for sublist in news_results for a in sublist]
    all_social = [p for sublist in social_results for p in sublist]
    all_weather = [w for w in weather_results if "error" not in w]

    print(
        f"\n{C.GREEN}✓ Fetched: {len(all_news)} news, {len(all_social)} social, {len(all_weather)} weather{C.RESET}\n"
    )

    # Sentiment
    all_text = " ".join(a["title"] for a in all_news + all_social)
    sentiment = simple_sentiment(all_text)

    # Fuse
    risk_cards = []
    if not args.dry_run and HAS_GROQ:
        print(f"{C.DIM}🧠 Fusing with Groq LLM...{C.RESET}")
        risk_cards = await fuse_with_groq(all_news, all_weather, all_social, config)

    if not risk_cards:
        print(f"{C.DIM}📊 Using rule-based risk scoring...{C.RESET}")
        for city_data in all_weather:
            card = rule_based_risk(
                news_count=len(all_news),
                weather=city_data,
                sentiment=sentiment,
                thresholds=config["thresholds"],
            )
            card["city"] = city_data["city"]
            card["disease"] = config["diseases"][0]
            card["recommendation"] = (
                "Continue monitoring"
                if card["risk_level"] == "LOW"
                else "Investigate signals"
            )
            risk_cards.append(card)

    # Output
    output_risk_card(risk_cards, len(all_news), len(all_weather), len(all_social))


if __name__ == "__main__":
    asyncio.run(main())
