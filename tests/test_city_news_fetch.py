"""City news: one throttled query must not blank a card that had evidence."""
import asyncio

import outbreak_sentinel as engine

CITIES = [{"name": "Karachi"}, {"name": "Lahore"}]
KARACHI_ITEMS = [{"title": "Karachi dengue cases rise", "link": "https://example.com/k"}]
LAHORE_ITEMS = [{"title": "Lahore dengue cases climb", "link": "https://example.com/l"}]


def _fresh():
    engine.clear_city_news_cache()


def _collect(fetcher, disease="dengue"):
    return asyncio.run(engine.gather_city_news(
        None, CITIES, fetcher, "dengue OR outbreak", 168, disease, delay=0
    ))


def test_single_429_is_retried_and_sources_survive():
    _fresh()
    calls = {}

    async def flaky(session, keyword, hours, city=None):
        calls[city] = calls.get(city, 0) + 1
        if city == "Lahore" and calls[city] == 1:
            return []  # a throttled query arrives as an empty body
        return LAHORE_ITEMS if city == "Lahore" else KARACHI_ITEMS

    results = _collect(flaky)

    assert results[0] == KARACHI_ITEMS
    assert results[1] == LAHORE_ITEMS
    assert calls["Lahore"] == 2
    assert calls["Karachi"] == 1


def test_retry_is_logged_per_city(capsys):
    _fresh()
    calls = {}

    async def flaky(session, keyword, hours, city=None):
        calls[city] = calls.get(city, 0) + 1
        if calls[city] == 1:
            return []
        return LAHORE_ITEMS

    _collect(flaky)
    out = capsys.readouterr().out
    assert "news city=Karachi items=1 retried=true" in out
    assert "news city=Lahore items=1 retried=true" in out


def test_cached_city_is_not_refetched():
    _fresh()
    calls = {}

    async def healthy(session, keyword, hours, city=None):
        calls[city] = calls.get(city, 0) + 1
        return KARACHI_ITEMS

    _collect(healthy)
    _collect(healthy)
    assert calls == {"Karachi": 1, "Lahore": 1}


def test_cache_key_includes_disease():
    _fresh()
    calls = {}

    async def healthy(session, keyword, hours, city=None):
        calls[city] = calls.get(city, 0) + 1
        return KARACHI_ITEMS

    _collect(healthy, disease="dengue")
    _collect(healthy, disease="malaria")
    assert calls == {"Karachi": 2, "Lahore": 2}


def test_transient_429_does_not_blank_a_warm_card():
    _fresh()
    calls = {}

    async def failing_after_warm(session, keyword, hours, city=None):
        calls[city] = calls.get(city, 0) + 1
        return LAHORE_ITEMS if calls[city] == 1 else []

    first = _collect(failing_after_warm)
    assert first[1] == LAHORE_ITEMS

    # Age the entry past its 10-minute TTL so the next call must go to the wire.
    key = engine.city_news_cache_key("Lahore", "dengue")
    engine._CITY_NEWS_CACHE[key]["at"] -= engine.CITY_NEWS_CACHE_TTL_S + 1

    second = _collect(failing_after_warm)
    assert second[1] == LAHORE_ITEMS
    assert calls["Lahore"] == 3  # warm fetch, then a miss plus one retry


def test_nothing_is_cached_when_the_query_stays_empty():
    _fresh()

    async def always_empty(session, keyword, hours, city=None):
        return []

    results = _collect(always_empty)
    assert results == [[], []]
    assert engine._CITY_NEWS_CACHE == {}
