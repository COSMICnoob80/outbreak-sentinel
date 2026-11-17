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
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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
        # Two tiers: Pakistan (home sentinel grid) then global reference cities.
        # "region" is propagated onto every risk card by the API layer.
        "cities": [
            {"name": "Karachi", "lat": 24.8607, "lon": 67.0011, "region": "pakistan"},
            {"name": "Lahore", "lat": 31.5204, "lon": 74.3587, "region": "pakistan"},
            {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479, "region": "pakistan"},
            {"name": "Peshawar", "lat": 34.0151, "lon": 71.5249, "region": "pakistan"},
            {"name": "Quetta", "lat": 30.1798, "lon": 66.9750, "region": "pakistan"},
            {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573, "region": "global"},
            {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723, "region": "global"},
            {"name": "Columbia", "lat": 34.0007, "lon": -81.0348, "region": "global"},
            {"name": "Anchorage", "lat": 61.2181, "lon": -149.9003, "region": "global"},
            {"name": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "region": "global"},
        ],
        "diseases": [
            "dengue", "malaria", "cholera", "typhoid", "hepatitis",
            "measles", "pertussis", "mpox",
        ],
        "news_keywords": [
            "dengue outbreak", "malaria cases", "cholera", "typhoid",
            "hepatitis", "fever outbreak", "hospital patients",
            "measles outbreak", "pertussis outbreak", "mpox cases",
        ],
        "social_keywords": [
            "dengue symptoms", "malaria symptoms", "fever", "sick",
            "hospital overflow", "patients", "whooping cough",
        ],
        # Per-disease topic vocabulary. A headline counts as evidence only when
        # it names the city AND matches one of these terms.
        "topic_terms": {
            "dengue": [
                "dengue", "dengue fever", "aedes", "mosquito", "outbreak",
                "vector", "cases", "hospitalised", "hospitalized",
            ],
            "malaria": [
                "malaria", "plasmodium", "anopheles", "mosquito", "outbreak",
                "cases", "fever", "hospitalised", "hospitalized",
            ],
            "cholera": [
                "cholera", "vibrio", "diarrhoea", "diarrhea", "waterborne",
                "outbreak", "cases", "hospitalised", "hospitalized",
            ],
            "typhoid": [
                "typhoid", "enteric fever", "salmonella", "outbreak", "cases",
                "fever", "hospitalised", "hospitalized",
            ],
            "hepatitis": [
                "hepatitis", "jaundice", "liver", "outbreak", "cases",
                "hospitalised", "hospitalized",
            ],
            "measles": [
                "measles", "rubeola", "outbreak", "cases", "vaccination",
                "vaccine", "hospitalised", "hospitalized",
            ],
            "pertussis": [
                "pertussis", "whooping cough", "cough", "outbreak", "cases",
                "vaccination", "vaccine", "hospitalised", "hospitalized",
            ],
            "mpox": [
                "mpox", "monkeypox", "outbreak", "cases", "clade",
                "hospitalised", "hospitalized",
            ],
            "default": [
                "outbreak", "cases", "fever", "infection", "disease",
                "hospitalised", "hospitalized",
            ],
        },
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
        # Wider window used ONLY for per-city news queries: a real city story
        # rarely lands inside 24h, and the shared diagnostic pool stays at 24h.
        "city_lookback_hours": 168,
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


# ── Geography ─────────────────────────────────────────────────────────
# News queries must be city-scoped. A bare city name is ambiguous for a few
# of them, so each maps to an explicit search phrase. The phrase is only a
# query expansion — matching still requires the city (or an unambiguous alias
# token) to appear in the headline.
CITY_ALIASES = {
    "Amsterdam": "Netherlands Amsterdam",
    "Netherlands": "Netherlands Amsterdam",
    "Columbia": "Columbia South Carolina",
    "South Carolina": "Columbia South Carolina",
    "Ludhiana": "Ludhiana Punjab India",
    "Amritsar": "Amritsar Punjab India",
    "Anchorage": "Anchorage Alaska",
    "Alaska": "Anchorage Alaska",
}

# Region words that must never by themselves attribute a headline to a city
# (e.g. "Punjab" is shared by Ludhiana and Amritsar).
_WEAK_ALIAS_TOKENS = {
    "india", "pakistan", "punjab", "south", "north", "state", "city",
    "region", "area", "county",
}


def city_query_phrase(city: str) -> str:
    """Search phrase that disambiguates a city for a news query."""
    name = str(city or "").strip()
    return CITY_ALIASES.get(name) or CITY_ALIASES.get(name.title()) or name


def city_match_terms(city: str) -> list[str]:
    """Tokens whose presence in a headline is evidence for this city."""
    name = str(city or "").strip().lower()
    terms = [name] if name else []
    phrase = city_query_phrase(city).lower()
    for token in re.findall(r"[a-z]+", phrase):
        if len(token) >= 4 and token not in terms and token not in _WEAK_ALIAS_TOKENS:
            terms.append(token)
    return terms


def title_mentions_city(title: str, city: str) -> bool:
    """True only when the headline itself names the city (word boundaries)."""
    text = str(title or "").lower()
    return any(re.search(rf"\b{re.escape(t)}\b", text) for t in city_match_terms(city))


def topic_terms_for(config: dict, disease: str) -> list[str]:
    """Vocabulary for the queried disease, falling back to a generic set."""
    table = (config or {}).get("topic_terms") or {}
    key = str(disease or "").strip().lower()
    terms = table.get(key) or table.get("default") or []
    return [str(t).strip().lower() for t in terms if str(t).strip()]


def title_matches_topic(title: str, disease: str, config: dict) -> bool:
    """True when the headline talks about the queried disease (word boundaries)."""
    text = str(title or "").lower()
    return any(
        re.search(rf"\b{re.escape(t)}\b", text)
        for t in topic_terms_for(config, disease)
    )


# ── Signal Fetchers ───────────────────────────────────────────────────


def rss_outlet(entry) -> str:
    """Publisher name from the RSS ``<source>`` element, else the link's host."""
    source = entry.get("source") if hasattr(entry, "get") else None
    title = ""
    href = ""
    if isinstance(source, dict):
        title = str(source.get("title") or "").strip()
        href = str(source.get("href") or "").strip()
    elif isinstance(source, str):
        title = source.strip()
    if title:
        return title
    if href:
        return urlsplit(href).hostname or ""
    return ""


def iso_published(entry) -> str:
    """Publish date as ``YYYY-MM-DD`` when the feed exposes a parseable date."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return ""
    try:
        return datetime(*parsed[:3]).date().isoformat()
    except (TypeError, ValueError):
        return ""


def lookback_label(lookback_hours: int) -> str:
    """Google News window token: ``168h`` silently returns nothing; ``7d`` works."""
    hours = int(lookback_hours or 0)
    if hours and hours % 24 == 0:
        return f"{hours // 24}d"
    return f"{hours}h"


async def fetch_news(
    session: aiohttp.ClientSession,
    keyword: str,
    lookback_hours: int,
    city: str | None = None,
) -> list[dict]:
    """Fetch news headlines via Google News RSS.

    When ``city`` is given the query is scoped to that city, and every item is
    tagged with its ``city`` so downstream code can tell city evidence apart
    from the shared diagnostic pool (``city`` is None there).
    """
    phrase = f"{city_query_phrase(city)} {keyword}" if city else keyword
    q = f"{phrase} when:{lookback_label(lookback_hours)}"
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
                "published": iso_published(entry),
                "outlet": rss_outlet(entry)
                or (urlsplit(entry.get("link", "")).hostname or ""),
                "city": city,
            }
            for entry in feed.entries[:20]
        ]
    except Exception as e:
        print(f"{C.DIM}  ⚠ News fetch failed for '{keyword}': {e}{C.RESET}")
        return []


async def gather_weather(
    session: aiohttp.ClientSession,
    cities: list,
    fetcher,
    attempts: int = 2,
    delay: float = 1.0,
) -> list:
    """Fetch weather for every city, retrying only the ones that failed.

    Downstream filters drop any result carrying an "error" key, so a single
    transient failure (e.g. a 429 during the concurrent news/weather/social
    burst) silently removes that city from the render. One retry round keeps
    the city grid stable without retrying successful fetches.
    """
    results = list(await asyncio.gather(*[fetcher(session, city) for city in cities]))
    for _ in range(1, attempts):
        failed = [
            i for i, r in enumerate(results)
            if not isinstance(r, dict) or "error" in r or "forecast" not in r
        ]
        if not failed:
            break
        if delay:
            await asyncio.sleep(delay)
        again = await asyncio.gather(*[fetcher(session, cities[i]) for i in failed])
        for i, r in zip(failed, again):
            results[i] = r
    return results


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
    """Fallback risk scoring when Groq is unavailable.

    ``news_count`` must be the CITY-SPECIFIC report count. Zero local reports
    means there is no evidence for this city: the pooled sentiment score is
    ignored, confidence is capped at 0.55, and benign weather forces LOW.
    """
    score = 0
    drivers = []
    local_reports = news_count > 0

    if news_count >= thresholds["news_high"]:
        score += 40
        drivers.append({"kind": "news", "text": f"News uptick: {news_count} articles in 24h"})
    elif news_count >= thresholds["news_medium"]:
        score += 20
        drivers.append({"kind": "news", "text": f"Moderate news: {news_count} articles in 24h"})

    forecast = weather.get("forecast", [])
    if forecast:
        max_rain = max((d.get("precipitation") or 0) for d in forecast)
        max_temp = max((d.get("temp_max") or 0) for d in forecast)
        if max_rain >= thresholds["rain_high"]:
            score += 20
            drivers.append({"kind": "weather", "text": f"Heavy rain forecast: {max_rain:.1f}mm"})
        if max_temp >= thresholds["temp_high"]:
            score += 15
            drivers.append({"kind": "weather", "text": f"High temperature: {max_temp:.1f}°C"})

    if local_reports:
        if sentiment >= thresholds["sentiment_high"]:
            score += 25
            drivers.append({"kind": "social", "text": f"High panic sentiment: {sentiment:.2f}"})
        elif sentiment >= thresholds["sentiment_medium"]:
            score += 10
            drivers.append({"kind": "social", "text": f"Moderate concern: {sentiment:.2f}"})
    else:
        drivers.insert(0, {"kind": "model", "text": "no city-specific outbreak signal"})

    if score >= 70:
        risk_level = "CRITICAL"
    elif score >= 50:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    confidence = min(0.95, 0.4 + score / 100)
    if not local_reports:
        # A weather-only read is not outbreak evidence, and pooled news from
        # other cities must never inflate it.
        confidence = min(confidence, 0.55)
        if score < 30:
            risk_level = "LOW"

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


LLM_TIMEOUT_SECONDS = 60
COMMANDCODE_BASE_URL = "https://api.commandcode.ai/provider/v1"
COMMANDCODE_DEFAULT_MODEL = "z-ai/glm-5.3-flash"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def llm_provider(config: dict | None = None) -> dict | None:
    """Pick the LLM backend from the environment, in priority order.

    1. ``CMDC_API_KEY``  → Command Code provider (OpenAI-compatible).
    2. ``GROQ_API_KEY``  → Groq, same model/key semantics as before.
    3. neither           → None (caller falls back to rule-based scoring).

    ``LLM_MODEL`` overrides the model id for the Command Code provider.
    Key material stays in the returned dict and is never logged.
    """
    model_override = (os.environ.get("LLM_MODEL") or "").strip() or None
    cmdc_key = (os.environ.get("CMDC_API_KEY") or "").strip()
    if cmdc_key:
        return {
            "name": "commandcode",
            "base_url": COMMANDCODE_BASE_URL,
            "model": model_override or COMMANDCODE_DEFAULT_MODEL,
            "api_key": cmdc_key,
        }
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if groq_key:
        groq_cfg = (config or {}).get("groq") or {}
        return {
            "name": "groq",
            "base_url": GROQ_BASE_URL,
            # LLM_MODEL is a Command Code override; Groq keeps its config model.
            "model": groq_cfg.get("model") or "openai/gpt-oss-120b",
            "api_key": groq_key,
        }
    return None


async def llm_chat(
    messages: list[dict],
    config: dict | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> dict:
    """One OpenAI-compatible chat completion, bounded by a 60s timeout.

    Returns ``{provider, model, ok, content, latency_ms, error}``. ``ok`` means
    the provider answered with a completion — never that the content parsed.
    A hung provider can never hang the request: the timeout forces ``ok=False``
    and the caller degrades to rule-based scoring.
    """
    provider = llm_provider(config)
    if not provider:
        return {
            "provider": None, "model": None, "ok": False,
            "content": None, "latency_ms": 0, "error": "no llm provider configured",
        }

    url = provider["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json",
        # Cloudflare fronts the provider and 403s (error 1010) a default UAs.
        "User-Agent": "outbreak-sentinel/1.0",
        "Accept": "application/json",
    }
    payload = {
        "model": provider["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    started = time.monotonic()
    content, ok, error = None, False, None
    try:
        timeout = aiohttp.ClientTimeout(total=LLM_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                if resp.status != 200:
                    error = f"HTTP {resp.status}"
                else:
                    data = json.loads(body)
                    choices = data.get("choices") or []
                    if choices:
                        ok = True
                        content = (choices[0].get("message") or {}).get("content")
                    else:
                        error = "empty choices"
    except asyncio.TimeoutError:
        error = f"timeout after {LLM_TIMEOUT_SECONDS}s"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    latency_ms = int((time.monotonic() - started) * 1000)
    print(
        f"LLM provider={provider['name']} model={provider['model']} "
        f"ok={str(ok).lower()} latency_ms={latency_ms}"
    )
    return {
        "provider": provider["name"],
        "model": provider["model"],
        "ok": ok,
        "content": content,
        "latency_ms": latency_ms,
        "error": error,
    }


async def fuse_with_llm(
    news_data: list, weather_data: list, social_data: list, config: dict
) -> list[dict]:
    """Fuse signals with the configured LLM provider."""
    if llm_provider(config) is None:
        print(f"{C.YELLOW}⚠ No LLM provider configured, using rule-based fallback{C.RESET}")
        return []

    vertical = config.get("_vertical") or {}
    forecast_vars = vertical.get("forecast_vars") or [
        "temperature_2m_max",
        "precipitation_sum",
        "weathercode",
    ]

    # City-scoped headlines first: the shared pool is context, not evidence.
    ordered_news = sorted(news_data, key=lambda a: 0 if a.get("city") else 1)
    news_summary = (
        "\n".join(
            f"- {a['title']}  [scope: {a.get('city') or 'shared diagnostic pool'}]"
            for a in ordered_news[:25]
        )
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

    monitored = ", ".join(
        str(c.get("name")) for c in (config.get("cities") or []) if c.get("name")
    ) or "no cities configured"
    prompt = f"""You are an {fusion_role}. Analyze these signals and produce risk cards.

MONITORED CITIES — output exactly one card per city below, in this order:
{monitored}

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
    "recommendation": "brief public health action",
    "summary": "2-3 sentence narrative explaining this risk, derived ONLY from the signals above"
  }}
]

Rules:
- Output exactly one card for every city in MONITORED CITIES. Never invent a city, region or country that is not in that list.
- GEOGRAPHY: Do not create a card for a city unless at least one source explicitly names that city; never attach a disease/death claim from another location.
- If a monitored city has no city-specific report, give it "LOW", confidence 0.4, drivers ["no city-specific outbreak signal"] and a summary saying it reflects weather only.
- Headlines tagged [scope: shared diagnostic pool] are NOT evidence for any city — use them only to understand the wider picture.
- Base every card, including each summary, strictly on the provided signals — never invent news, links or statistics
- {escalation or "Be conservative: only escalate if multiple signals align"}
- Consider the weather variables provided as relevant to the domain
- Consider news frequency: more articles = higher risk
- Consider sentiment: panic/fear words = higher risk

Output ONLY the JSON array, no other text."""

    result = await llm_chat(
        [{"role": "user", "content": prompt}],
        config=config,
        max_tokens=4096,
        temperature=0.2,
    )
    if not result["ok"]:
        print(f"{C.YELLOW}⚠ LLM fusion failed: {result.get('error')}{C.RESET}")
        return []
    if not result.get("content"):
        print(f"{C.YELLOW}⚠ LLM returned an empty completion{C.RESET}")
        return []
    parsed = _extract_json(result["content"])
    if parsed is None:
        print(f"{C.YELLOW}⚠ Could not parse LLM response as JSON{C.RESET}")
        return []
    if isinstance(parsed, dict):
        if "risk_cards" in parsed:
            return parsed["risk_cards"]
        return [parsed]
    return parsed


# Back-compat alias: the fusion path is provider-agnostic now.
fuse_with_groq = fuse_with_llm


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
                text = d.get("text") if isinstance(d, dict) else d
                print(f"     • {text}")
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

    outbreak_query = " OR ".join(list(config["diseases"]) + ["outbreak"])

    async with aiohttp.ClientSession() as session:
        # Shared diagnostic pool — never used as city evidence.
        print(f"{C.DIM}📰 Fetching news...{C.RESET}")
        news_results = await asyncio.gather(
            *[
                fetch_news(session, kw, config["lookback_hours"])
                for kw in config["news_keywords"]
            ]
        )
        # City-scoped news: one query per city, tagged with its city.
        # Uses the wider city window so real city stories are not cut off.
        city_hours = config.get("city_lookback_hours", config["lookback_hours"])
        city_news_results = await asyncio.gather(
            *[
                fetch_news(session, outbreak_query, city_hours, city=c["name"])
                for c in config["cities"]
            ]
        )

        # Fetch weather
        print(f"{C.DIM}🌤️  Fetching weather...{C.RESET}")
        _vertical = config.get("_vertical") or {}
        _forecast_vars = _vertical.get("forecast_vars") or None
        weather_results = await gather_weather(
            session,
            config["cities"],
            lambda s, city: fetch_weather(s, city, _forecast_vars),
        )

        # Fetch social
        print(f"{C.DIM}💬 Fetching social chatter...{C.RESET}")
        social_results = await asyncio.gather(
            *[fetch_social_chatter(session, kw) for kw in config["social_keywords"]]
        )

    # Flatten — shared pool plus city-scoped items (each tagged with its city).
    all_news = [a for sublist in news_results for a in sublist]
    all_news += [a for sublist in city_news_results for a in sublist]
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
    if not args.dry_run and llm_provider(config) is not None:
        provider = llm_provider(config)
        print(f"{C.DIM}🧠 Fusing with LLM ({provider['name']})...{C.RESET}")
        risk_cards = await fuse_with_llm(all_news, all_weather, all_social, config)

    if not risk_cards:
        print(f"{C.DIM}📊 Using rule-based risk scoring...{C.RESET}")
        for city_data in all_weather:
            city_news = [
                a for a in all_news
                if title_mentions_city(a.get("title"), city_data["city"])
                and title_matches_topic(
                    a.get("title"), config["diseases"][0], config
                )
            ]
            city_sentiment = simple_sentiment(" ".join(a.get("title", "") for a in city_news))
            card = rule_based_risk(
                news_count=len(city_news),
                weather=city_data,
                sentiment=city_sentiment,
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
