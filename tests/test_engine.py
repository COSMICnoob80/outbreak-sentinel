"""Deterministic engine: the requested disease is authoritative, the model narrates only."""
import asyncio

import pytest
from fastapi.testclient import TestClient

import app as app_module

KARACHI_DENGUE = {
    "title": "Karachi dengue cases rise sharply - The Express Tribune",
    "link": "https://example.com/karachi-dengue",
    "outlet": "The Express Tribune",
    "published": "2026-11-15",
    "city": "Karachi",
}
LAHORE_DENGUE = {
    "title": "Lahore dengue cases climb - Dawn",
    "link": "https://example.com/lahore-dengue",
    "outlet": "Dawn",
    "published": "2026-11-16",
    "city": "Lahore",
}


def _weather_all():
    return [
        {
            "city": city["name"],
            "forecast": [{"date": "2026-11-17", "precipitation": 0.0, "temp_max": 22.0}],
        }
        for city in app_module.CONFIG["cities"]
    ]


async def _signals():
    return [KARACHI_DENGUE, LAHORE_DENGUE], _weather_all(), [], 0.2


def _client(monkeypatch):
    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "collect_signals", _signals)
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")
    return TestClient(app_module.app)


@pytest.mark.parametrize("requested", ["dengue", "hepatitis c", "measles", "xyz"])
def test_every_card_carries_exactly_the_requested_disease(requested, monkeypatch):
    body = _client(monkeypatch).get("/risk", params={"disease": requested}).json()
    cards = body["risk_cards"]
    expected = app_module.display_disease(requested)
    assert expected.lower() == requested.lower()
    assert len(cards) == len(app_module.CONFIG["cities"])
    assert {card["disease"] for card in cards} == {expected}


def test_city_query_returns_one_card_with_its_own_sources(monkeypatch):
    body = _client(monkeypatch).get(
        "/risk", params={"city": "Karachi", "disease": "dengue"}
    ).json()
    cards = body["risk_cards"]
    assert len(cards) == 1
    assert cards[0]["city"] == "Karachi"
    assert cards[0]["disease"] == "Dengue"
    assert [source["title"] for source in cards[0]["sources"]] == [KARACHI_DENGUE["title"]]


def test_another_disease_headline_is_never_evidence():
    mpox = {
        "title": "Four Anchorage mpox cases have no reported travel - Medical Daily",
        "link": "https://example.com/anchorage-mpox",
        "outlet": "Medical Daily",
        "published": "2026-11-10",
        "city": "Anchorage",
    }
    assert app_module._pick_sources([mpox], "Anchorage", "dengue") == []


def test_multiword_disease_uses_its_head_noun_vocabulary():
    from outbreak_sentinel import topic_terms_for

    assert topic_terms_for(app_module.CONFIG, "hepatitis c") == topic_terms_for(
        app_module.CONFIG, "hepatitis"
    )
    headline = {
        "title": "Karachi hepatitis cases rise - Dawn",
        "link": "https://example.com/karachi-hepatitis",
        "outlet": "Dawn",
        "published": "2026-11-15",
        "city": "Karachi",
    }
    assert len(app_module._pick_sources([headline], "Karachi", "hepatitis c")) == 1


def test_same_story_from_two_outlets_is_cited_once():
    first = {
        "title": "Lahore struggles to shake off dengue - The Express Tribune",
        "link": "https://example.com/a",
        "outlet": "The Express Tribune",
        "published": "2026-11-16",
        "city": "Lahore",
    }
    second = {**first, "title": "Lahore struggles to shake off dengue - Dawn", "link": "https://example.com/b", "outlet": "Dawn"}
    picked = app_module._pick_sources([first, second], "Lahore", "dengue")
    assert len(picked) == 1


def test_two_live_builds_are_identical(monkeypatch):
    client = _client(monkeypatch)
    first = client.get("/risk", params={"disease": "dengue", "refresh": 1}).json()
    second = client.get("/risk", params={"disease": "dengue", "refresh": 1}).json()

    def view(body):
        return [
            (
                card["city"],
                card["disease"],
                card["risk_score"],
                tuple(source["title"] for source in card.get("sources") or []),
            )
            for card in body["risk_cards"]
        ]

    assert len(first["risk_cards"]) == len(app_module.CONFIG["cities"])
    assert view(first) == view(second)


def _narrated_card():
    card = {
        "city": "Karachi",
        "disease": "Dengue",
        "risk_level": "HIGH",
        "confidence": 0.7,
        "drivers": [{"kind": "news", "text": "Karachi dengue cases rise"}],
        "recommendation": "Monitor",
        "sources": [
            {
                "title": KARACHI_DENGUE["title"],
                "url": KARACHI_DENGUE["link"],
                "outlet": KARACHI_DENGUE["outlet"],
                "published": KARACHI_DENGUE["published"],
            }
        ],
        "risk_score": 55,
        "evidence_count": 1,
        "chart": [],
    }
    card["summary"] = app_module.deterministic_summary(card)
    return card


def _stub_narrator(monkeypatch, content):
    monkeypatch.setenv("SENTINEL_NARRATOR", "1")
    monkeypatch.setattr(
        app_module,
        "llm_provider",
        lambda config=None: {
            "name": "stub",
            "model": "stub",
            "base_url": "http://stub",
            "api_key": "test",
        },
    )

    async def fake_llm(messages, config=None, max_tokens=0, temperature=0):
        return {
            "provider": "stub",
            "model": "stub",
            "ok": True,
            "content": content,
            "latency_ms": 1,
            "error": None,
        }

    monkeypatch.setattr(app_module, "llm_chat", fake_llm)


def test_narrator_naming_another_city_is_discarded(monkeypatch):
    _stub_narrator(
        monkeypatch,
        '{"summary": "Lahore is the real dengue hotspot.", '
        '"recommendation": "Watch Lahore wards."}',
    )
    card = _narrated_card()
    expected = card["summary"]
    cards, narrated = asyncio.run(app_module.narrate_cards([card], "dengue"))
    assert narrated == 0
    assert cards[0]["summary"] == expected
    assert cards[0]["risk_level"] == "HIGH"


def test_narrator_naming_another_disease_is_discarded(monkeypatch):
    _stub_narrator(
        monkeypatch,
        '{"summary": "Karachi measles vaccination campaign expands.", '
        '"recommendation": "Monitor."}',
    )
    card = _narrated_card()
    expected = card["summary"]
    cards, narrated = asyncio.run(app_module.narrate_cards([card], "dengue"))
    assert narrated == 0
    assert cards[0]["summary"] == expected


def test_narrator_inventing_a_source_is_discarded(monkeypatch):
    _stub_narrator(
        monkeypatch,
        '{"summary": "Karachi dengue cases rise, see https://evil.example/story.", '
        '"recommendation": "Monitor."}',
    )
    card = _narrated_card()
    expected = card["summary"]
    cards, narrated = asyncio.run(app_module.narrate_cards([card], "dengue"))
    assert narrated == 0
    assert cards[0]["summary"] == expected


def test_narrator_may_change_level_by_one_step_only(monkeypatch):
    _stub_narrator(
        monkeypatch,
        '{"summary": "Karachi dengue reports keep rising.", '
        '"recommendation": "Reinforce ward surveillance.", "risk_level": "CRITICAL"}',
    )
    card = _narrated_card()
    cards, narrated = asyncio.run(app_module.narrate_cards([card], "dengue"))
    assert narrated == 1
    assert cards[0]["summary"] == "Karachi dengue reports keep rising."
    assert cards[0]["recommendation"] == "Reinforce ward surveillance."
    assert cards[0]["risk_level"] == "CRITICAL"


def test_narrator_two_step_level_jump_is_discarded(monkeypatch):
    _stub_narrator(
        monkeypatch,
        '{"summary": "Karachi dengue reports keep rising.", "risk_level": "LOW"}',
    )
    card = _narrated_card()
    expected = card["summary"]
    cards, narrated = asyncio.run(app_module.narrate_cards([card], "dengue"))
    assert narrated == 0
    assert cards[0]["risk_level"] == "HIGH"
    assert cards[0]["summary"] == expected
