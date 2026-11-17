"""Credibility gates: topic-matched sources, truthful signal kinds, grid cache."""
import time

from fastapi.testclient import TestClient

import app as app_module

ROBBERY = "Armed robbers target female medical students in Karachi - Bol News"
DENGUE = "Karachi dengue cases rise sharply - The Express Tribune"


def _news():
    return [
        {
            "title": ROBBERY,
            "link": "https://example.com/robbery",
            "outlet": "Bol News",
            "published": "2026-11-14",
            "city": "Karachi",
        },
        {
            "title": DENGUE,
            "link": "https://example.com/dengue",
            "outlet": "The Express Tribune",
            "published": "2026-11-15",
            "city": "Karachi",
        },
    ]


def _weather():
    return [{
        "city": "Karachi",
        "forecast": [{"date": "2026-11-17", "precipitation": 12.0, "temp_max": 30.0}],
    }]


async def _fake_collect_signals(disease="dengue"):
    return _news(), _weather(), [], 0.4


def _fake_rule_fuse(news, weather, social, sent, disease, city=None):
    cards = []
    for w in weather:
        card = app_module._norm_card(
            app_module.rule_based_risk(1, w, 0.1, app_module.CONFIG["thresholds"]),
            disease,
            w,
        )
        card["city"] = w["city"]
        cards.append(card)
    return cards, "rule-based"


def test_robbery_headline_is_never_a_dengue_source():
    titles = [s["title"] for s in app_module._pick_sources(_news(), "Karachi", "dengue")]
    assert titles == [DENGUE]
    assert not any("robber" in t.lower() for t in titles)


def test_dengue_card_sources_all_match_the_disease():
    card = {
        "city": "Karachi", "disease": "dengue", "risk_level": "MODERATE",
        "confidence": 0.5, "drivers": ["Karachi dengue cases rising"],
        "recommendation": "Monitor",
    }
    out = app_module._attach_card_extras(
        [card], _news(), {"karachi": _weather()[0]}, "dengue"
    )[0]
    assert out["sources"]
    assert all("dengue" in s["title"].lower() for s in out["sources"])
    assert not any("robber" in s["title"].lower() for s in out["sources"])


def test_zero_qualifying_sources_is_stated_plainly():
    card = {
        "city": "Karachi", "disease": "dengue", "risk_level": "MODERATE",
        "confidence": 0.5, "drivers": ["Karachi football result"],
        "recommendation": "Monitor",
    }
    out = app_module._attach_card_extras(
        [card], _news()[0:1], {"karachi": _weather()[0]}, "dengue"
    )[0]
    assert out["sources"] == []
    assert out["evidence_line"] == (
        "0 city-specific dengue reports in the last 7 days; "
        "risk reflects weather only."
    )


def test_every_driver_object_has_an_allowed_kind():
    card = app_module._norm_card({
        "city": "Karachi", "risk_level": "HIGH", "confidence": 0.8,
        "drivers": [
            {"kind": "weather", "text": "Heavy rain forecast"},
            "legacy string driver",
            {"kind": "made-up", "text": "Unknown provenance"},
        ],
        "recommendation": "Monitor",
    }, "dengue")
    assert card["drivers"]
    for driver in card["drivers"]:
        assert isinstance(driver, dict)
        assert driver["kind"] in app_module.ALLOWED_DRIVER_KINDS
        assert isinstance(driver["text"], str) and driver["text"]
    assert [d["kind"] for d in card["drivers"]] == ["weather", "model", "model"]


def test_rule_path_kinds_come_from_their_real_source():
    out = app_module.rule_based_risk(
        12,
        {"forecast": [{"precipitation": 60.0, "temp_max": 36.0}]},
        0.7,
        app_module.CONFIG["thresholds"],
    )
    assert [d["kind"] for d in out["drivers"]] == ["news", "weather", "weather", "social"]


def test_second_risk_call_is_cached(monkeypatch):
    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "collect_signals", _fake_collect_signals)
    monkeypatch.setattr(app_module, "_build_deterministic_cards", _fake_rule_fuse)
    client = TestClient(app_module.app)
    params = {"city": "Karachi", "disease": "dengue"}

    first = client.get("/risk", params=params)
    assert first.status_code == 200
    assert first.json()["cached"] is False

    started = time.monotonic()
    second = client.get("/risk", params=params)
    elapsed = time.monotonic() - started
    body = second.json()
    assert second.status_code == 200
    assert body["cached"] is True
    assert isinstance(body["cache_age_s"], int)
    assert elapsed < 2.0

    refreshed = client.get("/risk", params={**params, "refresh": 1})
    assert refreshed.status_code == 200
    assert refreshed.json()["cached"] is False
