"""Disease-term evidence: another disease's outbreak is never this card's evidence.

Regression for the false-HIGH London dengue card, built from three city-tagged
headlines: a dengue vector story, an Ebola story and a Legionnaires' story. The
city-scoped query is ``dengue OR outbreak``, so the old generic vocabulary
(``outbreak``/``cases``) counted all three. Only the disease term — or its
vector family — may now count.
"""
import app as app_module
import outbreak_sentinel as engine

# ── The London regression set ─────────────────────────────────────────
LONDON_VECTOR = (
    "UK steps up trapping efforts after mosquitoes that can spread dengue "
    "breed in London homes"
)
LONDON_EBOLA = "London hospital isolates patient as Ebola outbreak fears grow"
LONDON_LEGIONNAIRES = (
    "Legionnaires' disease outbreak investigated at London hotels"
)
LONDON_COVID = "London covid cases rise again as new variant spreads"


def _item(title, city, slug):
    return {
        "title": title,
        "link": f"https://example.com/{slug}",
        "outlet": "Example News",
        "published": "2026-11-24",
        "city": city,
    }


def _benign_forecast(city):
    return {
        "city": city,
        "forecast": [{"date": "2026-11-25", "precipitation": 0.0, "temp_max": 18.0}],
    }


def _build_bio_cards(news, disease="dengue"):
    weather = [_benign_forecast(c["name"]) for c in app_module.CONFIG["cities"]]
    cards, _ = app_module._build_deterministic_cards(news, weather, [], 0.1, disease)
    return app_module._attach_card_extras(
        cards, news, app_module._weather_by_city(weather), disease
    )


def test_london_card_counts_only_the_dengue_vector_story():
    news = [
        _item(LONDON_VECTOR, "London", "london-dengue-vector"),
        _item(LONDON_EBOLA, "London", "london-ebola"),
        _item(LONDON_LEGIONNAIRES, "London", "london-legionnaires"),
        _item(LONDON_COVID, "London", "london-covid"),
    ]
    picked = app_module._pick_sources(news, "London", "dengue")
    assert [s["title"] for s in picked] == [LONDON_VECTOR]


def test_london_card_is_never_high_on_other_diseases_outbreaks():
    news = [
        _item(LONDON_VECTOR, "London", "london-dengue-vector"),
        _item(LONDON_EBOLA, "London", "london-ebola"),
        _item(LONDON_LEGIONNAIRES, "London", "london-legionnaires"),
    ]
    card = next(c for c in _build_bio_cards(news) if c["city"] == "London")

    assert card["evidence_count"] == 1
    assert [s["title"] for s in card["sources"]] == [LONDON_VECTOR]
    assert card["risk_level"] in ("LOW", "MODERATE")
    assert card["risk_score"] < 50
    assert any(
        d.get("text") == "1 city-specific report in 7 days"
        for d in card["drivers"]
    )
    assert card["evidence_line"].startswith(
        "1 city-specific dengue report in the last 7 days"
    )
    for story in (LONDON_EBOLA, LONDON_LEGIONNAIRES):
        assert story not in [s["title"] for s in card["sources"]]


def test_other_disease_headlines_are_not_evidence_for_any_bio_card():
    for disease in ("dengue", "malaria", "cholera", "typhoid", "measles"):
        assert app_module._pick_sources(
            [_item(LONDON_EBOLA, "London", "ebola"), _item(LONDON_LEGIONNAIRES, "London", "legion")],
            "London",
            disease,
        ) == []


def test_karachi_with_genuinely_dengue_heavy_news_stays_high():
    headlines = [
        "Karachi dengue cases rise as ward 3 reports new infections",
        "Karachi dengue fever admissions climb at city hospitals",
        "Karachi dengue wards full as monsoon breeding sites spread",
        "Karachi dengue awareness drive targets mosquito hotspots",
        "Karachi dengue surveillance expanded across districts",
    ]
    news = [_item(title, "Karachi", f"karachi-{i}") for i, title in enumerate(headlines)]
    card = next(c for c in _build_bio_cards(news) if c["city"] == "Karachi")

    assert card["evidence_count"] == 5
    assert card["risk_level"] == "HIGH"
    assert any(
        d.get("text") == "5 city-specific reports in 7 days"
        for d in card["drivers"]
    )


def test_disease_term_matches_case_insensitively():
    news = [_item("KARACHI DENGUE UPDATE: new ward guidance issued", "Karachi", "ci")]
    assert len(app_module._pick_sources(news, "Karachi", "dengue")) == 1


def test_generic_outbreak_word_alone_is_not_evidence():
    news = [_item("Karachi outbreak response plan approved", "Karachi", "generic")]
    assert app_module._pick_sources(news, "Karachi", "dengue") == []


# ── Vector families ───────────────────────────────────────────────────
def test_vector_word_without_the_disease_name_counts_once_city_tagged():
    news = [_item("Delhi mosquitoes breed in stored water as cases climb", "Delhi", "vec")]
    assert len(app_module._pick_sources(news, "Delhi", "dengue")) == 1
    assert len(app_module._pick_sources(news, "Delhi", "malaria")) == 1
    assert app_module._pick_sources(news, "London", "dengue") == []


def test_water_and_sanitation_alone_are_not_cholera_evidence():
    news = [_item(
        "Karachi water supply contaminated after sanitation failures",
        "Karachi",
        "water",
    )]
    assert app_module._pick_sources(news, "Karachi", "cholera") == []
    assert app_module._pick_sources(news, "Karachi", "typhoid") == []


def test_cholera_is_evidence_when_the_disease_is_named():
    news = [_item("Karachi cholera cases traced to water supply", "Karachi", "cholera")]
    assert len(app_module._pick_sources(news, "Karachi", "cholera")) == 1


# ── Vertical hazard vocabulary ────────────────────────────────────────
def _vertical_cards(vertical, news, city="Los Angeles"):
    return app_module._build_vertical_cards(
        {vertical: {"cities": [{"name": city, "region": "global"}], "news": news}},
        {city.lower(): _benign_forecast(city)},
    )


def test_wildfire_requires_wildfire_vocabulary():
    news = [
        _item("Los Angeles blaze forces evacuations", "Los Angeles", "blaze"),
        _item("Los Angeles council approves new budget", "Los Angeles", "budget"),
    ]
    card = _vertical_cards("wildfire", news)[0]
    assert [s["title"] for s in card["sources"]] == ["Los Angeles blaze forces evacuations"]
    assert card["evidence_count"] == 1


def test_wildfire_smoke_headline_counts():
    news = [_item("Athens smoke blankets suburbs as fires burn", "Athens", "smoke")]
    card = _vertical_cards("wildfire", news, city="Athens")[0]
    assert card["evidence_count"] == 1


def test_supply_chain_requires_shortage_vocabulary():
    news = [
        _item("Lagos hospital stockout leaves clinics without drugs", "Lagos", "stockout"),
        _item("Lagos hospital opens a new wing", "Lagos", "wing"),
    ]
    card = _vertical_cards("supply-chain", news, city="Lagos")[0]
    assert [s["title"] for s in card["sources"]] == [
        "Lagos hospital stockout leaves clinics without drugs"
    ]
    assert card["evidence_count"] == 1


def test_supply_chain_shortage_headline_counts():
    news = [_item("Lagos medicine shortage hits rural clinics", "Lagos", "shortage")]
    card = _vertical_cards("supply-chain", news, city="Lagos")[0]
    assert card["evidence_count"] == 1


# ── Config honesty ────────────────────────────────────────────────────
def test_evidence_vocabulary_is_declared_in_defaults_and_yaml():
    defaults = engine.default_config()
    assert defaults["evidence_terms"]["dengue"] == ["dengue"]
    assert defaults["vector_terms"]["dengue"] == ["mosquito", "mosquitoes", "aedes"]
    assert set(defaults["evidence_terms"]) == set(defaults["diseases"])
    assert app_module.CONFIG["evidence_terms"] == defaults["evidence_terms"]
    assert app_module.CONFIG["vector_terms"] == defaults["vector_terms"]
