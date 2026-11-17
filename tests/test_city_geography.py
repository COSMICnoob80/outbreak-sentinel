"""Geography gate: a headline from another place must never become a city's evidence."""
import app as app_module

AIJKER = "Dengue death toll crosses 500 as 3 more die - Aijker Patrika"

NEWS = [
    {"title": AIJKER, "link": "https://example.com/global", "city": None},
    {"title": "Karachi dengue cases rise sharply", "link": "https://example.com/karachi",
     "city": "Karachi"},
]

BENIGN_WEATHER = {
    "city": "Amsterdam",
    "forecast": [{"date": "2026-11-17", "precipitation": 0.0, "temp_max": 18.0}],
}


def test_global_headline_is_not_amsterdam_evidence():
    assert app_module._pick_sources(NEWS, "Amsterdam", "dengue") == []


def test_global_headline_is_not_tagged_as_amsterdam():
    assert app_module._city_news(NEWS, "Amsterdam") == []


def test_city_headline_is_kept():
    titles = [s["title"] for s in app_module._pick_sources(NEWS, "Karachi", "dengue")]
    assert titles == ["Karachi dengue cases rise sharply"]


def test_query_tag_alone_is_not_evidence():
    tagged_junk = [{"title": "Pakistan inflation expected to ease", "link": "u", "city": "Karachi"}]
    assert app_module._pick_sources(tagged_junk, "Karachi", "dengue") == []
    assert app_module._city_news(tagged_junk, "Karachi") == []


def test_alias_headline_counts_for_city():
    news = [{"title": "Dengue cases in the Netherlands climb", "link": "https://example.com/nl"}]
    assert len(app_module._pick_sources(news, "Amsterdam", "dengue")) == 1


def test_context_source_is_labelled_and_capped_at_one():
    context = [
        {"title": AIJKER, "link": "https://example.com/global"},
        {"title": "Another global dengue story", "link": "https://example.com/other"},
    ]
    picked = app_module._pick_sources(NEWS, "Amsterdam", "dengue", context=context)
    assert len(picked) == 1
    assert picked[0]["context"] is True
    assert picked[0]["title"].startswith("context — not evidence for this city:")


def test_no_local_signal_forces_low_confidence():
    card = app_module.rule_based_risk(0, BENIGN_WEATHER, 0.91, app_module.CONFIG["thresholds"])
    assert card["risk_level"] == "LOW"
    assert card["confidence"] <= 0.55
    assert "no city-specific outbreak signal" in card["drivers"]


def test_llm_card_without_local_evidence_is_downgraded():
    weather_map = {"amsterdam": BENIGN_WEATHER}
    card = {
        "city": "Amsterdam",
        "disease": "dengue",
        "risk_level": "HIGH",
        "confidence": 0.91,
        "drivers": ["Dengue death toll crosses 500"],
        "recommendation": "Escalate",
    }
    out = app_module._attach_card_extras([card], NEWS, weather_map, "dengue")[0]
    assert out["risk_level"] == "LOW"
    assert out["confidence"] <= 0.55
    assert out["sources"] == []
