"""Citations: a card only shows sources that name its own city, fully attributed."""
import os

import pytest
from fastapi.testclient import TestClient

import app as app_module

AJKER = "Dengue death toll crosses 500 as 3 more die - Ajker Patrika"
AJKER_ITEM = {
    "title": AJKER,
    "link": "https://www.ajkerpatrika.com/example",
    "outlet": "Ajker Patrika",
    "published": "2026-11-14",
    "city": None,
}

KARACHI_ITEMS = [
    {
        "title": "Karachi outpaces rest of Sindh in dengue cases - The Express Tribune",
        "link": "https://tribune.com.pk/story/karachi-dengue",
        "outlet": "The Express Tribune",
        "published": "2026-11-12",
        "city": "Karachi",
    },
    {
        "title": "Karachi dengue surge continues - The Express Tribune",
        "link": "https://tribune.com.pk/story/dengue-surge",
        "outlet": "The Express Tribune",
        "published": "2026-11-15",
        "city": "Karachi",
    },
    {
        # Real Karachi query result, but the headline names no city -> never a citation.
        "title": "The dengue surge - The Express Tribune",
        "link": "https://tribune.com.pk/story/unscoped-surge",
        "outlet": "The Express Tribune",
        "published": "2026-11-15",
        "city": "Karachi",
    },
]

BENIGN_WEATHER = {
    "city": "Karachi",
    "forecast": [{"date": "2026-11-17", "precipitation": 0.0, "temp_max": 20.0}],
}


@pytest.mark.parametrize("city", ["Amsterdam", "Karachi", "Lahore"])
def test_ajker_patrika_never_attaches_to_a_city(city):
    news = [AJKER_ITEM]
    assert app_module._pick_sources(news, city, "dengue") == []
    card = {
        "city": city, "disease": "dengue", "risk_level": "HIGH",
        "confidence": 0.9, "drivers": ["Dengue death toll crosses 500"],
        "recommendation": "Escalate",
    }
    out = app_module._attach_card_extras(
        [card], news, {city.lower(): {**BENIGN_WEATHER, "city": city}}, "dengue"
    )[0]
    assert out["sources"] == []


def test_karachi_headline_attaches_with_outlet_and_published():
    picked = app_module._pick_sources(KARACHI_ITEMS[:1], "Karachi", "dengue")
    assert len(picked) == 1
    assert picked[0]["outlet"] == "The Express Tribune"
    assert picked[0]["published"] == "2026-11-12"
    assert picked[0]["url"] == "https://tribune.com.pk/story/karachi-dengue"


def test_card_evidence_line_counts_city_reports():
    card = {
        "city": "Karachi", "disease": "dengue", "risk_level": "MODERATE",
        "confidence": 0.6, "drivers": ["Karachi dengue cases rising"],
        "recommendation": "Monitor",
    }
    out = app_module._attach_card_extras(
        [card], KARACHI_ITEMS, {"karachi": BENIGN_WEATHER}, "dengue"
    )[0]
    assert out["evidence_line"] == (
        "2 city-specific dengue reports in the last 7 days \u2014 latest 15 Nov."
    )
    assert all(s["outlet"] and s["published"] for s in out["sources"])


def test_card_without_city_reports_is_honest():
    card = {
        "city": "Amsterdam", "disease": "dengue", "risk_level": "HIGH",
        "confidence": 0.9, "drivers": ["Dengue death toll crosses 500"],
        "recommendation": "Escalate",
    }
    out = app_module._attach_card_extras(
        [card], [AJKER_ITEM], {"amsterdam": {**BENIGN_WEATHER, "city": "Amsterdam"}},
        "dengue",
    )[0]
    assert out["evidence_line"] == (
        "0 city-specific dengue reports in the last 7 days; risk reflects weather only."
    )


@pytest.mark.skipif(
    not os.environ.get("CMDC_API_KEY"),
    reason="CMDC_API_KEY not present; live provider check skipped",
)
def test_intel_llm_reports_ok_with_provider_key():
    client = TestClient(app_module.app)
    body = client.get("/intel/llm").json()
    assert body["provider"] == "commandcode"
    assert body["model"]
    assert body["ok"] is True
    assert isinstance(body["latency_ms"], int)
    assert body["checked_at"]
