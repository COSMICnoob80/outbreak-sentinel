"""Wildfire + supply-chain verticals: real cards, config sanity, concurrency."""
import asyncio

from fastapi.testclient import TestClient

import app as app_module
import outbreak_sentinel as engine


# ── Config sanity ─────────────────────────────────────────────────────

def _assert_city_grid(cities, expected_count):
    assert len(cities) == expected_count
    for city in cities:
        assert city.get("name")
        assert isinstance(city.get("lat"), (int, float))
        assert isinstance(city.get("lon"), (int, float))
        assert city.get("region") in ("pakistan", "global")


def test_main_grid_is_14_cities_with_complete_geo():
    _assert_city_grid(app_module.CONFIG["cities"], 14)


def test_wildfire_grid_is_6_cities_with_complete_geo():
    _assert_city_grid(app_module.CONFIG["wildfire_cities"], 6)


def test_default_config_mirrors_the_yaml_grid():
    defaults = engine.default_config()
    assert len(defaults["cities"]) == 14
    assert len(defaults["wildfire_cities"]) == 6
    assert defaults["wildfire_query"] == "wildfire OR bushfire"
    assert "medicine shortage" in defaults["supply_chain_query"]


# ── Wildfire drivers ──────────────────────────────────────────────────

def _forecast(temp, rain, wind):
    return {"city": "Los Angeles", "forecast": [{
        "date": "2026-11-22",
        "temp_max": temp,
        "precipitation": rain,
        "wind_max": wind,
    }]}


def test_hot_dry_windy_forecast_yields_three_drivers():
    drivers = engine.wildfire_weather_drivers(_forecast(35.0, 0.0, 30.0))
    texts = " ".join(d["text"] for d in drivers)
    assert "Hot forecast" in texts
    assert "Dry 7-day outlook" in texts
    assert "High wind" in texts
    assert all(d["kind"] == "weather" for d in drivers)


def test_cool_wet_calm_forecast_yields_no_drivers():
    assert engine.wildfire_weather_drivers(_forecast(20.0, 25.0, 5.0)) == []


def test_wildfire_card_with_no_reports_and_no_driver_is_low():
    cards = app_module._build_vertical_cards(
        {"wildfire": {"cities": [{"name": "Los Angeles", "region": "global"}], "news": []}},
        {"los angeles": _forecast(20.0, 25.0, 5.0)},
    )
    card = cards[0]
    assert card["vertical"] == "wildfire"
    assert card["disease"] is None
    assert card["risk_level"] == "LOW"
    assert card["sources"] == []
    assert card["drivers"][0]["text"] == "no city-specific wildfire signal"


def test_wildfire_card_uses_real_city_report_and_drivers():
    news = [{
        "title": "Los Angeles wildfire forces evacuations",
        "link": "https://example.com/la-fire",
        "outlet": "Example News",
        "published": "2026-11-20",
        "city": "Los Angeles",
    }]
    cards = app_module._build_vertical_cards(
        {"wildfire": {"cities": [{"name": "Los Angeles", "region": "global"}], "news": news}},
        {"los angeles": _forecast(36.0, 0.5, 40.0)},
    )
    card = cards[0]
    assert card["evidence_count"] == 1
    assert card["sources"][0]["title"] == news[0]["title"]
    texts = " ".join(d["text"] for d in card["drivers"])
    assert "city-specific wildfire report" in texts
    assert "Hot forecast" in texts and "High wind" in texts
    assert card["risk_level"] in ("MODERATE", "HIGH", "CRITICAL")


def test_wildfire_headline_without_the_hazard_is_not_evidence():
    news = [{
        "title": "Los Angeles council approves new budget",
        "link": "https://example.com/la-budget",
        "outlet": "Example News",
        "published": "2026-11-20",
        "city": "Los Angeles",
    }]
    cards = app_module._build_vertical_cards(
        {"wildfire": {"cities": [{"name": "Los Angeles", "region": "global"}], "news": news}},
        {"los angeles": _forecast(20.0, 25.0, 5.0)},
    )
    assert cards[0]["sources"] == []
    assert cards[0]["risk_level"] == "LOW"


# ── Supply chain ──────────────────────────────────────────────────────

def test_supply_chain_card_from_one_report_stays_low():
    news = [{
        "title": "Lagos medicine shortage hits clinics",
        "link": "https://example.com/lagos-meds",
        "outlet": "Example News",
        "published": "2026-11-20",
        "city": "Lagos",
    }]
    cards = app_module._build_vertical_cards(
        {"supply-chain": {"cities": [{"name": "Lagos", "region": "global"}], "news": news}},
        {},
    )
    card = cards[0]
    assert card["vertical"] == "supply-chain"
    assert card["disease"] is None
    assert card["evidence_count"] == 1
    assert card["risk_level"] == "LOW"


def test_supply_chain_card_with_no_report_is_honest_empty():
    cards = app_module._build_vertical_cards(
        {"supply-chain": {"cities": [{"name": "Lagos", "region": "global"}], "news": []}},
        {},
    )
    card = cards[0]
    assert card["risk_level"] == "LOW"
    assert card["sources"] == []
    assert card["evidence_line"].startswith("0 city-specific supply-chain reports")


# ── Concurrency gate ──────────────────────────────────────────────────

def test_shared_semaphore_caps_concurrency_and_does_not_deadlock():
    engine.clear_city_news_cache()
    cities = [{"name": f"GateCity{i}"} for i in range(18)]
    state = {"current": 0, "peak": 0, "calls": 0}

    async def fetcher(session, keyword, hours, city=None):
        state["calls"] += 1
        state["current"] += 1
        state["peak"] = max(state["peak"], state["current"])
        try:
            await asyncio.sleep(0.005)
            return [{
                "title": f"{city} outbreak reported",
                "link": f"https://example.com/{city}",
            }]
        finally:
            state["current"] -= 1

    gate = asyncio.Semaphore(engine.CITY_FETCH_CONCURRENCY)
    results = asyncio.run(engine.gather_city_news(
        None, cities, fetcher, "dengue OR outbreak", 168, "dengue",
        delay=0, semaphore=gate,
    ))

    assert len(results) == 18
    assert all(results)
    assert state["calls"] == 18
    assert state["peak"] <= engine.CITY_FETCH_CONCURRENCY


# ── /risk contract ───────────────────────────────────────────────────

KARACHI_DENGUE = {
    "title": "Karachi dengue cases rise sharply",
    "link": "https://example.com/karachi-dengue",
    "outlet": "The Express Tribune",
    "published": "2026-11-20",
    "city": "Karachi",
}
LA_WILDFIRE = {
    "title": "Los Angeles wildfire forces evacuations",
    "link": "https://example.com/la-fire",
    "outlet": "Example News",
    "published": "2026-11-20",
    "city": "Los Angeles",
}
LAGOS_SHORTAGE = {
    "title": "Lagos medicine shortage hits clinics",
    "link": "https://example.com/lagos-meds",
    "outlet": "Example News",
    "published": "2026-11-20",
    "city": "Lagos",
}


def test_risk_exposes_all_three_vertical_card_types(monkeypatch):
    async def signals(disease="dengue"):
        weather = [
            {"city": c["name"], "forecast": [{
                "date": "2026-11-22", "temp_max": 36.0,
                "precipitation": 0.0, "wind_max": 30.0,
            }]}
            for c in app_module._unique_cities(
                app_module.CONFIG["cities"] + app_module.CONFIG["wildfire_cities"]
            )
        ]
        vertical_signals = {
            "wildfire": {
                "cities": [{"name": "Los Angeles", "region": "global"}],
                "news": [LA_WILDFIRE],
            },
            "supply-chain": {
                "cities": [{"name": "Lagos", "region": "global"}],
                "news": [LAGOS_SHORTAGE],
            },
        }
        return [KARACHI_DENGUE], weather, [], 0.1, vertical_signals

    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "collect_signals", signals)
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")
    body = TestClient(app_module.app).get(
        "/risk", params={"disease": "dengue", "refresh": 1}
    ).json()

    by_vertical = {}
    for card in body["risk_cards"]:
        by_vertical.setdefault(card["vertical"], []).append(card)

    assert "bio-surveillance" in by_vertical
    assert by_vertical["wildfire"][0]["disease"] is None
    assert by_vertical["wildfire"][0]["city"] == "Los Angeles"
    assert by_vertical["supply-chain"][0]["disease"] is None
    assert by_vertical["supply-chain"][0]["city"] == "Lagos"
    assert all(card["vertical"] for card in body["risk_cards"])
