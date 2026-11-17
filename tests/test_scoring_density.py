"""Density scoring: city evidence moves the level, and no evidence cannot."""
import json

from fastapi.testclient import TestClient

import app as app_module
import outbreak_sentinel as engine

THRESHOLDS = app_module.CONFIG["thresholds"]
BENIGN = {"city": "Karachi", "forecast": [{"date": "2026-11-17", "precipitation": 0.0, "temp_max": 22.0}]}
WET = {"city": "Lahore", "forecast": [{"date": "2026-11-17", "precipitation": 62.0, "temp_max": 24.0}]}


def _reports(city, count, disease="dengue"):
    return [
        {
            "title": f"{city} {disease} cases rise in ward {n} - The Express Tribune",
            "link": f"https://example.com/{city.lower()}/{n}",
            "outlet": "The Express Tribune",
            "published": "2026-11-16",
            "city": city,
        }
        for n in range(count)
    ]


def test_density_bands_come_from_config():
    bands = THRESHOLDS["evidence_density"]
    assert {(b["min_reports"], b["points"]) for b in bands} == {
        (1, 20), (2, 30), (3, 40), (5, 55),
    }


def test_score_rises_with_report_density():
    scores = {n: engine.rule_based_risk(n, {"forecast": []}, 0.0, THRESHOLDS)["score"]
              for n in (0, 1, 2, 3, 4, 5, 9)}
    assert scores[0] == 0
    assert scores[1] == 20
    assert scores[2] == 30
    assert scores[3] == scores[4] == 40
    assert scores[5] == scores[9] == 55


def test_two_city_reports_are_moderate_or_better():
    card = engine.rule_based_risk(2, BENIGN, 0.0, THRESHOLDS)
    assert card["score"] >= 30
    assert card["risk_level"] == "MODERATE"


def test_three_city_reports_with_vector_weather_reach_high():
    card = engine.rule_based_risk(3, WET, 0.0, THRESHOLDS)
    assert card["score"] >= 50
    assert card["risk_level"] == "HIGH"


def test_no_city_reports_stays_low_with_capped_confidence():
    card = engine.rule_based_risk(0, WET, 0.91, THRESHOLDS)
    assert card["risk_level"] == "LOW"
    assert card["score"] < 30
    assert card["confidence"] <= 0.55
    assert any("no city-specific outbreak signal" in d["text"] for d in card["drivers"])


def test_score_is_capped_at_one_hundred():
    card = engine.rule_based_risk(9, WET, 0.9, THRESHOLDS)
    assert card["score"] <= 100
    assert card["risk_level"] == "CRITICAL"


def test_driver_names_the_real_window_from_config():
    card = engine.rule_based_risk(3, BENIGN, 0.0, THRESHOLDS)
    hours = app_module.CONFIG["city_lookback_hours"]
    expected = f"3 city-specific reports in {engine.window_label(hours)}"
    assert [d["text"] for d in card["drivers"] if d["kind"] == "news"] == [expected]
    assert "articles in 24h" not in json.dumps(card)


def _weather_for_all():
    return [
        {
            "city": c["name"],
            "forecast": [{"date": "2026-11-17", "precipitation": 62.0, "temp_max": 24.0}],
        }
        for c in app_module.CONFIG["cities"]
    ]


async def _signals(disease="dengue"):
    news = _reports("Karachi", 2) + _reports("Lahore", 3)
    return news, _weather_for_all(), [], 0.0


def _client(monkeypatch):
    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "collect_signals", _signals)
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")
    return TestClient(app_module.app)


def test_grid_shows_evidence_driven_levels(monkeypatch):
    body = _client(monkeypatch).get("/risk", params={"disease": "dengue"}).json()
    by_city = {card["city"]: card for card in body["risk_cards"]}

    karachi, lahore = by_city["Karachi"], by_city["Lahore"]
    assert karachi["risk_level"] in ("MODERATE", "HIGH", "CRITICAL")
    assert karachi["risk_score"] >= 30
    assert len(karachi["sources"]) == 2
    assert lahore["risk_level"] in ("HIGH", "CRITICAL")
    assert lahore["risk_score"] >= 50
    assert len(lahore["sources"]) == 3

    assert by_city["Quetta"]["risk_level"] == "LOW"
    assert by_city["Quetta"]["confidence"] <= 0.55
    assert by_city["Quetta"]["sources"] == []
    assert len({c["risk_level"] for c in body["risk_cards"]}) > 1


def test_one_story_from_two_outlets_counts_once_everywhere(monkeypatch):
    story = "Lahore struggles to shake off dengue"
    duplicated = [
        {**_reports("Lahore", 1)[0], "title": f"{story} - The Express Tribune",
         "link": "https://example.com/a", "outlet": "The Express Tribune"},
        {**_reports("Lahore", 1)[0], "title": f"{story} - Dawn",
         "link": "https://example.com/b", "outlet": "Dawn"},
    ]

    async def signals(disease="dengue"):
        return duplicated, _weather_for_all(), [], 0.0

    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "collect_signals", signals)
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")
    card = TestClient(app_module.app).get(
        "/risk", params={"city": "Lahore", "disease": "dengue"}
    ).json()["risk_cards"][0]

    news_driver = next(d for d in card["drivers"] if d["kind"] == "news")
    assert news_driver["text"].startswith("1 city-specific report ")
    assert card["evidence_count"] == len(card["sources"]) == 1
    assert card["evidence_line"].startswith("1 city-specific dengue report in the last 7 days")


def test_repeated_live_builds_are_byte_identical(monkeypatch):
    client = _client(monkeypatch)
    first = client.get("/risk", params={"disease": "dengue", "refresh": 1}).json()
    second = client.get("/risk", params={"disease": "dengue", "refresh": 1}).json()
    assert json.dumps(first["risk_cards"], sort_keys=True) == json.dumps(
        second["risk_cards"], sort_keys=True
    )
