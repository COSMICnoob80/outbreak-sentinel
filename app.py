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
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from receipts import ReceiptStore, make_receipt
from publish import publish_cards
from outbreak_sentinel import default_config, fuse_with_groq, gather_weather, load_env_file

app = FastAPI(title="Outbreak Sentinel", version="1.0.0")

# ── Config ─────────────────────────────────────────────────────────────

def load_config(path: str = "config.yaml") -> dict:
    config_path = os.path.join(os.path.dirname(__file__), path)
    # Single source of truth: the engine's defaults (no duplicated city grid).
    defaults = default_config()
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
        weather = await gather_weather(session, CONFIG["cities"], fetch_weather)
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
    # Optional extras (additive, backwards-compatible):
    sources: Optional[list[dict]] = None       # [{title, url}] — real news items
    summary: Optional[str] = None              # LLM narrative (or rule-based when LLM down)
    chart: Optional[list[dict]] = None         # [{label, value}] — 7-day forecast sparkline
    illustration_hint: Optional[str] = None    # machine string for dashboard art
    region: Optional[str] = None               # "pakistan" | "global" (from city config)

class RiskResponse(BaseModel):
    timestamp: str
    signals: dict
    risk_cards: list[RiskCard]
    engine: Optional[str] = None  # "llm" | "rule-based" — honest about path taken


_CARD_KEYS = ("city", "disease", "risk_level", "confidence", "drivers", "recommendation")
_CARD_EXTRA_KEYS = ("sources", "summary", "chart", "illustration_hint", "region")
_CARD_FIELDS = _CARD_KEYS + _CARD_EXTRA_KEYS


def _norm_card(c: dict, disease: str, fallback: dict | None = None) -> dict:
    """Coerce a card (LLM or rule-based) into the exact RiskCard shape."""
    base = fallback or {}
    level = str(c.get("risk_level") or base.get("risk_level") or "LOW").upper()
    if level not in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        level = "LOW"
    conf = float(c.get("confidence", base.get("confidence", 0.5)))
    if conf > 1:
        conf = conf / 100.0
    drivers = c.get("drivers") or base.get("drivers") or []
    if isinstance(drivers, str):
        drivers = [drivers]
    card = {
        "city": str(c.get("city") or base.get("city") or "Unknown"),
        "disease": str(c.get("disease") or disease),
        "risk_level": level,
        "confidence": max(0.0, min(1.0, conf)),
        "drivers": [str(d) for d in drivers][:6],
        "recommendation": str(c.get("recommendation") or base.get("recommendation") or "Investigate signals"),
    }
    # Pass through optional fused-engine extras when the LLM supplied them.
    summary = str(c.get("summary") or base.get("summary") or "").strip()
    if summary:
        card["summary"] = summary
    for key in ("sources", "chart", "illustration_hint"):
        if c.get(key):
            card[key] = c[key]
    return card


def _weather_by_city(weather: list) -> dict:
    return {w["city"].lower(): w for w in weather if isinstance(w, dict) and w.get("city") and "forecast" in w}


def _region_by_city() -> dict:
    """Configured city name -> region. Unconfigured (LLM-invented) cities are global."""
    return {
        str(c.get("name", "")).strip().lower(): str(c.get("region") or "global")
        for c in CONFIG.get("cities", [])
    }


def _pick_sources(news: list, city: str, disease: str, limit: int = 5) -> list[dict]:
    """Real news items from collect_signals, matching the card's city then disease."""
    city_low, disease_low = city.lower(), disease.lower()
    seen, picked = set(), []
    ranked = []
    ranked = [n for n in news if city_low in (n.get("title") or "").lower()]
    ranked += [n for n in news if disease_low in (n.get("title") or "").lower()]
    for n in ranked:
        key = (n.get("title") or "", n.get("link") or "")
        if key in seen:
            continue
        seen.add(key)
        picked.append({"title": n.get("title") or "", "url": n.get("link") or ""})
        if len(picked) >= limit:
            break
    return picked


def _sparkline(weather: dict | None) -> list[dict]:
    """7-day forecast sparkline (real open-meteo data): precipitation over next week."""
    if not isinstance(weather, dict):
        return []
    out = []
    for d in (weather.get("forecast") or [])[:7]:
        val = d.get("precipitation")
        if val is None:
            continue
        out.append({"label": str(d.get("date", "")), "value": round(float(val), 1)})
    return out


def _illustration_hint(card: dict, weather: dict | None) -> str:
    level = (card.get("risk_level") or "LOW").lower()
    disease = str(card.get("disease") or "disease").lower()
    cue = "clear"
    forecast = (weather or {}).get("forecast", [])
    if forecast:
        max_rain = max((d.get("precipitation") or 0) for d in forecast)
        max_temp = max((d.get("temp_max") or 0) for d in forecast)
        if max_rain >= 10:
            cue = "rain"
        elif max_temp >= 35:
            cue = "heat"
    return f"{disease}-{cue}-{level}"


def _attach_card_extras(cards: list, news: list, weather_map: dict, disease: str) -> list:
    """Attach sources/summary/chart/illustration_hint — additive, authentic only."""
    regions = _region_by_city()
    for card in cards:
        city = card.get("city", "Unknown")
        card["region"] = regions.get(str(city).strip().lower(), "global")
        w = weather_map.get(str(city).lower())
        if card.get("sources") is None:
            card["sources"] = _pick_sources(news, str(city), disease)
        if card.get("chart") is None:
            card["chart"] = _sparkline(w)
        if card.get("illustration_hint") is None:
            card["illustration_hint"] = _illustration_hint(card, w)
        if not card.get("summary"):
            drivers = card.get("drivers") or []
            top = "; ".join(drivers[:2]) if drivers else "no strong signals in the lookback window"
            card["summary"] = (
                f"{city} shows {card.get('risk_level', 'LOW')} risk for {card.get('disease', disease)}: {top}."
            )
    return cards


async def _fuse_or_rule_based(news, weather, social, sent, disease, city=None):
    """LLM fusion FIRST — the real agentic path."""
    fused = []
    try:
        fused = await asyncio.wait_for(fuse_with_groq(news, weather, social, CONFIG), timeout=90) or []
    except Exception:
        fused = []
    if fused:
        cards = [_norm_card(c, disease) for c in fused if isinstance(c, dict) and c.get("risk_level")]
        if city:
            cards = [c for c in cards if c["city"].lower() == city.lower()]
        if cards:
            return cards, "llm"
    cards = []
    for w in weather:
        card = _norm_card(rule_based_risk(len(news), w, sent, CONFIG["thresholds"]), disease, w)
        card["city"] = w["city"]
        if city is None or w["city"].lower() == city.lower():
            cards.append(card)
    return cards, "rule-based"


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    """Canonical entry point: the Operations Console."""
    return RedirectResponse(url="/telegraph/dashboard", status_code=302)

@app.get("/risk", response_model=RiskResponse)
async def get_risk(city: Optional[str] = None, disease: str = "dengue"):
    """Get outbreak risk cards. Filter by city and/or disease.

    Runs the real LLM fusion path. Rule-based scoring is used only when the LLM
    is unavailable; the `engine` field reports which path ran.
    """
    try:
        news, weather, social, sent = await asyncio.wait_for(collect_signals(), timeout=30)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Signal collection timed out")

    cards, engine = await _fuse_or_rule_based(news, weather, social, sent, disease, city)
    cards = _attach_card_extras(cards, news, _weather_by_city(weather), disease)
    if city and not cards:
        raise HTTPException(status_code=404, detail=f"No data for city: {city}")

    now = datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M PKT")
    return RiskResponse(
        timestamp=now,
        signals={"news": len(news), "social": len(social), "cities": len(weather)},
        risk_cards=[RiskCard(**{k: c[k] for k in _CARD_FIELDS if k in c}) for c in cards],
        engine=engine,
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
    # Settlement must never 500 this endpoint: any failure degrades to a non-500
    # payload that states what went wrong in `settlement_error`.
    settlement_error = None
    try:
        proof = await _telegraph_client.buy_intelligence(
            req.query, context={"city": req.city, "disease": req.disease, "vertical": req.vertical}
        )
    except Exception as exc:
        settlement_error = f"{type(exc).__name__}: {exc}"
        proof = {
            "mode": "live" if is_live() else "mocked",
            "live": False,
            "ranked_answer": None,
            "miner": None,
            "miner_name": None,
            "amount": None,
            "tx_hash": None,
            "network_label": TELEGRAPH_CONFIG["network_label"],
            "chain_id": TELEGRAPH_CONFIG["chain_id"],
            "testnet_boundary": TELEGRAPH_CONFIG["testnet_boundary"],
        }

    # Build the resulting risk card via the real LLM fusion path (additive reuse).
    risk_card = None
    engine = None
    try:
        news, weather, social, sent = await asyncio.wait_for(collect_signals(), timeout=30)
        weather_map = _weather_by_city(weather)
        cards, engine = await _fuse_or_rule_based(news, weather, social, sent, req.disease, req.city)
        cards = _attach_card_extras(cards, news, weather_map, req.disease)
        if cards:
            risk_card = dict(cards[0])
            risk_card["city"] = req.city or risk_card["city"]
        elif weather:
            w = weather[0]
            risk_card = _norm_card(rule_based_risk(len(news), w, sent, CONFIG["thresholds"]), req.disease, w)
            risk_card["city"] = w["city"]
            risk_card["disease"] = req.disease
            engine = "rule-based"
            risk_card = _attach_card_extras([risk_card], news, weather_map, req.disease)[0]
    except Exception as exc:  # never fail the demo endpoint on signal hiccups
        risk_card = {"error": str(exc)}

    # Every settlement field is read defensively — a missing key is reported, not raised.
    settlement = proof.get("settlement") or {}
    try:
        settlement_view = {
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
        }
    except Exception as exc:
        if settlement_error is None:
            settlement_error = f"{type(exc).__name__}: {exc}"
        settlement_view = {
            "miner": settlement.get("miner"),
            "miner_name": settlement.get("miner_name"),
            "amount": settlement.get("amount_usd"),
            "amount_uusdc": settlement.get("amount_uusdc"),
            "tx_hash": settlement.get("tx_hash"),
            "network_label": settlement.get("network_label"),
            "chain_id": settlement.get("chain_id"),
            "rail": settlement.get("rail"),
            "receipt_hash": settlement.get("receipt_hash"),
            "real_challenge_received": settlement.get("real_challenge_received"),
            "mocked": settlement.get("mocked"),
        }
    if proof.get("error"):
        settlement_error = str(proof["error"])

    return {
        "request": {"query": req.query, "city": req.city, "disease": req.disease, "vertical": req.vertical},
        "mode": proof.get("mode"),
        "live": proof.get("live", False),
        "ranked_answer": proof.get("ranked_answer"),
        # Money-visible (first-class):
        "miner": proof.get("miner"),
        "miner_name": proof.get("miner_name"),
        "amount": proof.get("amount"),
        "tx_hash": proof.get("tx_hash"),
        "network_label": proof.get("network_label"),
        "chain_id": proof.get("chain_id"),
        "settlement": settlement_view,
        "settlement_error": settlement_error,
        "risk_card": risk_card,
        "engine": engine,
        "testnet_boundary": proof.get("testnet_boundary", TELEGRAPH_CONFIG["testnet_boundary"]),
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
    """Serve the Operations Console."""
    path = os.path.join(os.path.dirname(__file__), "dashboard", "index.html")
    return FileResponse(path, media_type="text/html")


@app.get("/telegraph/buying-layer")
def telegraph_buying_layer():
    """Demo page for the Track 03 buying layer — not the default landing page."""
    path = os.path.join(os.path.dirname(__file__), "static", "telegraph.html")
    return FileResponse(path, media_type="text/html")


# ── Static file mounts (PWA + dashboard) — additive ─────────────────────
from fastapi.staticfiles import StaticFiles

_dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(_dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")

_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
