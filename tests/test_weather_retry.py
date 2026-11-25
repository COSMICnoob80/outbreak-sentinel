import asyncio

from outbreak_sentinel import WEATHER_FETCH_CONCURRENCY, gather_weather

CITIES = [{"name": f"City{i}", "lat": 0.0, "lon": 0.0} for i in range(10)]
FAILING = {"City3", "City7", "City9"}


def _ok(city):
    return {"city": city["name"], "forecast": [{"date": "2026-10-22", "precipitation": 0.0}]}


def _error(city, status=429):
    return {"city": city["name"], "error": f"HTTP {status}"}


def test_transient_failure_is_retried_and_recovers():
    calls = {}

    async def flaky(session, city):
        calls[city["name"]] = calls.get(city["name"], 0) + 1
        if city["name"] in FAILING and calls[city["name"]] == 1:
            return _error(city)
        return _ok(city)

    results = asyncio.run(gather_weather(None, CITIES, flaky, delay=0))

    assert len(results) == len(CITIES)
    assert all("forecast" in r and "error" not in r for r in results)
    assert all(calls[c] == 2 for c in FAILING)
    assert all(calls[c["name"]] == 1 for c in CITIES if c["name"] not in FAILING)


def test_successful_run_does_not_retry():
    calls = {}

    async def healthy(session, city):
        calls[city["name"]] = calls.get(city["name"], 0) + 1
        return _ok(city)

    results = asyncio.run(gather_weather(None, CITIES, healthy, delay=0))

    assert len(results) == len(CITIES)
    assert set(calls.values()) == {1}


def test_permanent_failure_respects_attempt_budget():
    calls = {}

    async def always_down(session, city):
        calls[city["name"]] = calls.get(city["name"], 0) + 1
        return _error(city, status=503)

    results = asyncio.run(gather_weather(None, CITIES, always_down, attempts=3, delay=0))

    assert all("error" in r for r in results)
    assert set(calls.values()) == {3}


def test_weather_fetch_concurrency_is_bounded():
    cities = [{"name": f"BurstCity{i}", "lat": 0.0, "lon": 0.0} for i in range(20)]
    state = {"current": 0, "peak": 0}

    async def fetcher(session, city):
        state["current"] += 1
        state["peak"] = max(state["peak"], state["current"])
        try:
            await asyncio.sleep(0.005)
            return _ok(city)
        finally:
            state["current"] -= 1

    results = asyncio.run(gather_weather(None, cities, fetcher, delay=0))

    assert len(results) == len(cities)
    assert all("forecast" in r for r in results)
    assert state["peak"] <= WEATHER_FETCH_CONCURRENCY


def test_retry_after_header_lengthens_the_wait(monkeypatch):
    waits = []
    real_sleep = asyncio.sleep

    async def fake_sleep(seconds):
        waits.append(seconds)
        await real_sleep(0)

    monkeypatch.setattr("outbreak_sentinel.asyncio.sleep", fake_sleep)
    calls = {}

    async def limited(session, city):
        calls[city["name"]] = calls.get(city["name"], 0) + 1
        if calls[city["name"]] == 1:
            return {**_error(city, status=429), "retry_after": 17}
        return _ok(city)

    city = {"name": "City0", "lat": 0.0, "lon": 0.0}
    results = asyncio.run(gather_weather(None, [city], limited, delay=2.0))

    assert "forecast" in results[0]
    assert waits == [17]
