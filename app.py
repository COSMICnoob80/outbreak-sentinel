"""
Outbreak Sentinel — Telegraph Season II Service
Machine-consumable outbreak risk intelligence API.
"""
import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiohttp
import feedparser
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from receipts import ReceiptStore, make_receipt
from publish import publish_cards

app = FastAPI(title="Outbreak Sentinel", version="1.0.0")

# ── Config ─────────────────────────────────────────────────────────────

def load_config(path: str = "config.yaml") -> dict:
    config_path = os.path.join(os.path.dirname(__file__), path)
    defaults = {
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
            "news_high": 10, "news_medium": 5,
            "sentiment_high": 0.6, "sentiment_medium": 0.3,
            "temp_high": 35.0, "rain_high": 50.0,
        },
        "groq": {"model": "llama-3.3-70b-versatile", "api_key_env": "GROQ_API_KEY"},
        "lookback_hours": 24,
    }
    if not os.path.exists(config_path):
        return defaults
    with open(config_path) as f:
        user = yaml.safe_load(f) or {}
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(defaults.get(k), dict):
            defaults[k].update(v)
        else:
            defaults[k] = v
    return defaults

CONFIG = load_config()

# ── Signal fetchers ───────────────────────────────────────────────────

async def fetch_news(session, keyword, hours):
    q = f"{keyword} pakistan when:{hours}h"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return []
            feed = feedparser.parse(await r.text())
            return [{"title": e.get("title", ""), "link": e.get("link", "")} for e in feed.entries[:20]]
    except Exception:
        return []

async def fetch_weather(session, city):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"], "longitude": city["lon"],
        "daily": "temperature_2m_max,precipitation_sum,weathercode",
        "timezone": "Asia/Karachi", "forecast_days": 7,
    }
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return {"city": city["name"], "error": f"HTTP {r.status}"}
            data = await r.json()
            daily = data.get("daily", {})
            times = daily.get("time", [])
            forecast = [{"date": times[i],
                          "temp_max": daily.get("temperature_2m_max", [None]*len(times))[i],
                          "temp_min": daily.get("temperature_2m_min", [None]*len(times))[i],
                          "precipitation": daily.get("precipitation_sum", [None]*len(times))[i],
                          "weathercode": daily.get("weathercode", [None]*len(times))[i]}
                         for i in range(len(times))]
            return {"city": city["name"], "forecast": forecast}
    except Exception as e:
        return {"city": city["name"], "error": str(e)}

PANIC_WORDS = {"outbreak", "epidemic", "panic", "crisis", "emergency", "surge", "spike", "death", "died", "fatal", "deadly"}
FEAR_WORDS = {"fear", "worried", "concern", "alarm", "warning", "alert", "danger", "threat", "scared", "horrific"}
HOPE_WORDS = {"recover", "recovering", "discharge", "treatment", "vaccine", "prevention", "control", "contained", "stable"}

def sentiment_score(text):
    t = text.lower()
    score = (sum(1 for w in PANIC_WORDS if w in t) * 2 + sum(1 for w in FEAR_WORDS if w in t) - sum(1 for w in HOPE_WORDS if w in t) * 0.5) / 10
    return max(0.0, min(1.0, score))

def rule_based_risk(news_count, weather, sent, thresholds):
    score = 0
    drivers = []
    if news_count >= thresholds["news_high"]:
        score += 40; drivers.append(f"News uptick: {news_count} articles in 24h")
    elif news_count >= thresholds["news_medium"]:
        score += 20; drivers.append(f"Moderate news: {news_count} articles in 24h")
    forecast = weather.get("forecast", [])
    if forecast:
        max_rain = max((d.get("precipitation") or 0) for d in forecast)
        max_temp = max((d.get("temp_max") or 0) for d in forecast)
        if max_rain >= thresholds["rain_high"]:
            score += 20; drivers.append(f"Heavy rain forecast: {max_rain:.1f}mm")
        if max_temp >= thresholds["temp_high"]:
            score += 15; drivers.append(f"High temperature: {max_temp:.1f}°C")
    if sent >= thresholds["sentiment_high"]:
        score += 25; drivers.append(f"High panic sentiment: {sent:.2f}")
    elif sent >= thresholds["sentiment_medium"]:
        score += 10; drivers.append(f"Moderate concern: {sent:.2f}")
    if score >= 70: level = "CRITICAL"
    elif score >= 50: level = "HIGH"
    elif score >= 30: level = "MODERATE"
    else: level = "LOW"
    return {"risk_level": level, "score": score, "confidence": round(min(0.95, 0.4 + score/100), 2), "drivers": drivers}

async def collect_signals():
    hours = CONFIG["lookback_hours"]
    async with aiohttp.ClientSession() as session:
        news = await asyncio.gather(*[fetch_news(session, kw, hours) for kw in CONFIG["news_keywords"]])
        weather = await asyncio.gather(*[fetch_weather(session, c) for c in CONFIG["cities"]])
        social = await asyncio.gather(*[fetch_news(session, kw, 24) for kw in CONFIG["social_keywords"]])
    all_news = [a for sub in news for a in sub]
    all_social = [p for sub in social for p in sub]
    all_weather = [w for w in weather if "error" not in w]
    all_text = " ".join(a["title"] for a in all_news + all_social)
    return all_news, all_weather, all_social, sentiment_score(all_text)

# ── API Models ────────────────────────────────────────────────────────

class RiskCard(BaseModel):
    city: str
    disease: str
    risk_level: str
    confidence: float
    drivers: list[str]
    recommendation: str

class RiskResponse(BaseModel):
    timestamp: str
    signals: dict
    risk_cards: list[RiskCard]

# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "service": "outbreak-sentinel", "version": "1.0.0", "cities": [c["name"] for c in CONFIG["cities"]]}

@app.get("/risk", response_model=RiskResponse)
async def get_risk(city: Optional[str] = None, disease: str = "dengue"):
    """Get outbreak risk cards. Filter by city and/or disease."""
    try:
        news, weather, social, sent = await asyncio.wait_for(collect_signals(), timeout=30)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Signal collection timed out")

    cards = []
    for w in weather:
        card = rule_based_risk(len(news), w, sent, CONFIG["thresholds"])
        card["city"] = w["city"]
        card["disease"] = disease
        card["recommendation"] = "Continue monitoring" if card["risk_level"] == "LOW" else "Investigate signals"
        if city is None or w["city"].lower() == city.lower():
            cards.append(RiskCard(**card))

    if city and not cards:
        raise HTTPException(status_code=404, detail=f"No data for city: {city}")

    now = datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M PKT")
    return RiskResponse(
        timestamp=now,
        signals={"news": len(news), "social": len(social), "cities": len(weather)},
        risk_cards=cards,
    )

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "history", "receipts.jsonl")
STORE = ReceiptStore(LEDGER_PATH)


@app.get("/receipts")
def list_receipts(status: Optional[str] = None):
    items = STORE.all()
    if status:
        items = [r for r in items if r.get("status") == status.upper()]
    return {"count": len(items), "receipts": items}


@app.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: str):
    r = STORE.get(receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="receipt not found")
    return r


@app.get("/scoreboard")
def scoreboard():
    resolved = [r for r in STORE.all() if r.get("status") == "RESOLVED"]
    verdicts: dict[str, int] = {}
    for r in resolved:
        v = r["resolution"]["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    return {"total_receipts": STORE.count(), "resolved": len(resolved),
            "verdicts": verdicts}


@app.get("/cities")
def list_cities():
    return {"cities": [c["name"] for c in CONFIG["cities"]]}

@app.get("/diseases")
def list_diseases():
    return {"diseases": CONFIG["diseases"]}


# ── Channel adapters: universal inbound hook + health check ───────────

from adapters import fan_out
from outbreak_sentinel import load_env_file

load_env_file()


class AlertCard(BaseModel):
    city: str
    disease: str
    risk_level: str
    confidence: float
    drivers: list[str] = []
    recommendation: str = ""
    receipt_id: Optional[str] = None


@app.post("/alerts")
async def post_alert(card: AlertCard):
    """Fan a posted risk card out through every configured channel."""
    results = await fan_out(card.model_dump(exclude_none=True))
    return {
        "accepted": True,
        "channels": results,
        "delivered": sum(1 for ok in results.values() if ok),
        "total": len(results),
    }


@app.get("/health")
def health_check():
    """Liveness probe that reports honestly, including Groq key resolution."""
    key_env = CONFIG.get("groq", {}).get("api_key_env", "GROQ_API_KEY")
    key = os.environ.get(key_env)
    return {
        "status": "ok",
        "service": "outbreak-sentinel",
        "version": app.version,
        "groq_key_present": bool(key and key.strip()),
    }


# ── Telegraph buying layer (Track 03: Apps & Agents) ─────────────────────
# Additive only. The agent BUYS ranked intelligence through Telegraph.

from telegraph.config import TELEGRAPH_CONFIG, is_live
from telegraph.client import TelegraphClient

_telegraph_client = TelegraphClient()


class TelegraphRiskRequest(BaseModel):
    query: str = "Assess outbreak risk for the monitored cities"
    city: Optional[str] = None
    disease: str = "dengue"
    vertical: Optional[str] = None


@app.post("/telegraph/risk")
async def telegraph_risk(req: TelegraphRiskRequest):
    """Track 03 demo endpoint: route a PAID Telegraph request, return ranked
    answer + settlement proof + resulting risk card. Money-visible fields are
    first-class JSON keys."""
    proof = await _telegraph_client.buy_intelligence(
        req.query, context={"city": req.city, "disease": req.disease, "vertical": req.vertical}
    )

    # Build the resulting risk card using the existing engine (additive reuse).
    risk_card = None
    try:
        news, weather, social, sent = await asyncio.wait_for(collect_signals(), timeout=30)
        for w in weather:
            if req.city is not None and w["city"].lower() != req.city.lower():
                continue
            card = rule_based_risk(len(news), w, sent, CONFIG["thresholds"])
            card["city"] = w["city"]
            card["disease"] = req.disease
            card["recommendation"] = "Continue monitoring" if card["risk_level"] == "LOW" else "Investigate signals"
            risk_card = card
            break
        if risk_card is None and weather:
            w = weather[0]
            card = rule_based_risk(len(news), w, sent, CONFIG["thresholds"])
            card["city"] = w["city"]
            card["disease"] = req.disease
            card["recommendation"] = "Continue monitoring" if card["risk_level"] == "LOW" else "Investigate signals"
            risk_card = card
    except Exception as exc:  # never fail the demo endpoint on signal hiccups
        risk_card = {"error": str(exc)}

    settlement = proof["settlement"]
    return {
        "request": {"query": req.query, "city": req.city, "disease": req.disease, "vertical": req.vertical},
        "mode": proof["mode"],
        "live": proof["live"],
        "ranked_answer": proof["ranked_answer"],
        # Money-visible (first-class):
        "miner": proof["miner"],
        "miner_name": proof["miner_name"],
        "amount": proof["amount"],
        "tx_hash": proof["tx_hash"],
        "network_label": proof["network_label"],
        "chain_id": proof["chain_id"],
        "settlement": {
            "miner": settlement["miner"],
            "miner_name": settlement["miner_name"],
            "amount": settlement["amount_usd"],
            "amount_uusdc": settlement["amount_uusdc"],
            "tx_hash": settlement["tx_hash"],
            "network_label": settlement["network_label"],
            "chain_id": settlement["chain_id"],
            "rail": settlement["rail"],
            "receipt_hash": settlement["receipt_hash"],
            "real_challenge_received": settlement["real_challenge_received"],
            "mocked": settlement["mocked"],
        },
        "risk_card": risk_card,
        "testnet_boundary": proof["testnet_boundary"],
    }


@app.get("/telegraph/status")
def telegraph_status():
    """Testnet boundary stated on screen, unprompted."""
    return {
        "live": is_live(),
        "is_live": is_live(),
        "mode": "live" if is_live() else "mocked (Mechanism)",
        "settlement_mode": TELEGRAPH_CONFIG["settlement_mode"],
        "network_label": TELEGRAPH_CONFIG["network_label"],
        "chain_id": TELEGRAPH_CONFIG["chain_id"],
        "chain_caip": TELEGRAPH_CONFIG["chain_caip"],
        "usdc_address": TELEGRAPH_CONFIG["usdc_address"],
        "rpc_url": TELEGRAPH_CONFIG["rpc_url"],
        "explorer_tx_url": TELEGRAPH_CONFIG["explorer_tx_url"],
        "price_source": TELEGRAPH_CONFIG["price_source"],
        "miner_selection": TELEGRAPH_CONFIG["miner_selection"],
        "testnet": True,
        "testnet_boundary": TELEGRAPH_CONFIG["testnet_boundary"],
        "last_settlement": _telegraph_client.last_proof,
        "last_settlement_proof": _telegraph_client.last_proof,
    }


@app.get("/telegraph/intents")
async def telegraph_intents():
    """Return available intents from the live miner discovery endpoint (real call)."""
    import aiohttp as _aiohttp
    url = TELEGRAPH_CONFIG["engine_url"].rstrip("/") + "/v1/intents"
    try:
        async with _aiohttp.ClientSession() as session:
            async with session.get(url, timeout=_aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200:
                    raise HTTPException(status_code=502, detail=f"intents endpoint HTTP {r.status}")
                data = await r.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    intents = data.get("intents", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return {
        "source": "live",
        "real": True,
        "count": data.get("count", len(intents)) if isinstance(data, dict) else len(intents),
        "canonical_on_chain": data.get("canonical_on_chain") if isinstance(data, dict) else None,
        "with_miners": data.get("with_miners") if isinstance(data, dict) else None,
        "intents": intents,
    }


@app.get("/telegraph/dashboard")
def telegraph_dashboard():
    """Serve the money-visible front-end fragment."""
    from fastapi.responses import FileResponse
    import os as _os
    path = _os.path.join(_os.path.dirname(__file__), "static", "telegraph.html")
    return FileResponse(path, media_type="text/html")


# ── Static file mounts (PWA + dashboard) — additive ─────────────────────
from fastapi.staticfiles import StaticFiles

_dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(_dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")

_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
