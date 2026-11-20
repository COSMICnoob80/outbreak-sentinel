"""Weather grid cache: TTL hit, TTL expiry, and force-clear refetch."""
import asyncio

import outbreak_sentinel as engine

CITIES = [{"name": f"City{i}", "lat": 0.0, "lon": 0.0} for i in range(3)]


def _ok(city):
    return {
        "city": city["name"],
        "forecast": [{"date": "2026-11-20", "precipitation": 0.0}],
    }


def _run(fetcher, now):
    return asyncio.run(engine.gather_weather_cached(None, CITIES, fetcher, now=now))


def test_cache_hit_within_ttl_skips_network():
    engine.clear_weather_cache()
    calls = []

    async def healthy(session, city):
        calls.append(city["name"])
        return _ok(city)

    first = _run(healthy, now=100.0)
    second = _run(healthy, now=100.0 + engine.WEATHER_CACHE_TTL_S - 1)

    assert second == first
    assert len(calls) == len(CITIES)


def test_cache_expiry_refetches():
    engine.clear_weather_cache()
    calls = []

    async def healthy(session, city):
        calls.append(city["name"])
        return _ok(city)

    _run(healthy, now=0.0)
    _run(healthy, now=engine.WEATHER_CACHE_TTL_S + 1)

    assert len(calls) == len(CITIES) * 2


def test_clear_weather_cache_forces_refetch():
    engine.clear_weather_cache()
    calls = []

    async def healthy(session, city):
        calls.append(city["name"])
        return _ok(city)

    _run(healthy, now=0.0)
    engine.clear_weather_cache()
    _run(healthy, now=1.0)

    assert len(calls) == len(CITIES) * 2
