"""MET Norway fallback: adapter fold, trigger, provider record, stale cache.

The fixture below is a verbatim slice of a real
``api.met.no/weatherapi/locationforecast/2.0/compact`` response for
lat=34.05 lon=-118.24, probed 2026-11-25 (HTTP 200, 41082 bytes), trimmed to
five consecutive hours spanning one UTC midnight.
"""
import asyncio

import pytest

import app as app_module
from app import forecast_from_met

MET_FIXTURE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [34.05, -118.24, 0]},
    "properties": {
        "meta": {"updated_at": "2026-11-25T14:41:23Z", "units": {"air_temperature": "celsius"}},
        "timeseries": [
            {
                "time": "2026-11-25T22:00:00Z",
                "data": {
                    "instant": {"details": {
                        "air_pressure_at_sea_level": 1017.2,
                        "air_temperature": 21.4,
                        "cloud_area_fraction": 2.3,
                        "relative_humidity": 27.3,
                        "wind_from_direction": 233.5,
                        "wind_speed": 2.4,
                    }},
                    "next_1_hours": {
                        "summary": {"symbol_code": "clearsky_day"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
            {
                "time": "2026-11-25T23:00:00Z",
                "data": {
                    "instant": {"details": {
                        "air_pressure_at_sea_level": 1017.1,
                        "air_temperature": 21.2,
                        "cloud_area_fraction": 2.3,
                        "relative_humidity": 28.5,
                        "wind_from_direction": 260.2,
                        "wind_speed": 1.9,
                    }},
                    "next_1_hours": {
                        "summary": {"symbol_code": "clearsky_day"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
            {
                "time": "2026-11-26T00:00:00Z",
                "data": {
                    "instant": {"details": {
                        "air_pressure_at_sea_level": 1017.1,
                        "air_temperature": 19.7,
                        "cloud_area_fraction": 0.0,
                        "relative_humidity": 45.3,
                        "wind_from_direction": 271.2,
                        "wind_speed": 1.9,
                    }},
                    "next_1_hours": {
                        "summary": {"symbol_code": "clearsky_day"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
            {
                "time": "2026-11-26T01:00:00Z",
                "data": {
                    "instant": {"details": {
                        "air_pressure_at_sea_level": 1017.5,
                        "air_temperature": 18.0,
                        "cloud_area_fraction": 0.0,
                        "relative_humidity": 48.8,
                        "wind_from_direction": 328.7,
                        "wind_speed": 1.5,
                    }},
                    "next_1_hours": {
                        "summary": {"symbol_code": "clearsky_night"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
            {
                "time": "2026-11-26T02:00:00Z",
                "data": {
                    "instant": {"details": {
                        "air_pressure_at_sea_level": 1017.7,
                        "air_temperature": 16.2,
                        "cloud_area_fraction": 0.0,
                        "relative_humidity": 54.5,
                        "wind_from_direction": 18.5,
                        "wind_speed": 2.3,
                    }},
                    "next_1_hours": {
                        "summary": {"symbol_code": "clearsky_night"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
        ],
    },
}

CITY = {"name": "Los Angeles", "lat": 34.05, "lon": -118.24}

OPEN_METEO_PAYLOAD = {
    "daily": {
        "time": ["2026-11-25", "2026-11-26"],
        "temperature_2m_max": [22.0, 20.0],
        "temperature_2m_min": [12.0, 11.0],
        "precipitation_sum": [0.0, 1.2],
        "weathercode": [0, 3],
        "windspeed_10m_max": [9.0, 7.0],
    }
}


class _Response:
    def __init__(self, status=200, payload=None, text="", headers=None):
        self.status = status
        self._payload = payload
        self._text = text
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return self._text


class _Session:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.handler(url, kwargs)


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    monkeypatch.delenv("OPEN_METEO_API_KEY", raising=False)
    app_module._WEATHER_ATTEMPTS.clear()
    app_module._WEATHER_LAST_GOOD.clear()
    yield
    app_module._WEATHER_ATTEMPTS.clear()
    app_module._WEATHER_LAST_GOOD.clear()


def _run(coro):
    return asyncio.run(coro)


def test_forecast_from_met_folds_real_fixture_by_utc_day():
    forecast = forecast_from_met(MET_FIXTURE)

    assert [day["date"] for day in forecast] == ["2026-11-25", "2026-11-26"]
    first, second = forecast
    assert first["temp_max"] == 21.4
    assert first["temp_min"] == 21.2
    assert first["precipitation"] == 0.0
    assert first["wind_max"] == 8.6  # 2.4 m/s -> km/h
    assert first["weathercode"] == 1  # clearsky -> clear
    assert second["temp_max"] == 19.7
    assert second["temp_min"] == 16.2
    assert second["wind_max"] == 8.3  # 2.3 m/s -> km/h
    assert set(first) == {
        "date", "temp_max", "temp_min", "precipitation", "weathercode", "wind_max",
    }


def test_open_meteo_429_falls_back_to_met_norway():
    def handler(url, kwargs):
        if "open-meteo" in url:
            return _Response(
                status=429,
                payload={},
                text='{"reason":"Daily API request limit exceeded. Please try again tomorrow."}',
                headers={"Retry-After": "33545"},
            )
        return _Response(status=200, payload=MET_FIXTURE)

    session = _Session(handler)
    result = _run(app_module.fetch_weather(session, CITY))

    assert "error" not in result
    assert result["provider"] == "met-norway"
    assert [day["date"] for day in result["forecast"]] == ["2026-11-25", "2026-11-26"]
    met_calls = [url for url, _ in session.calls if "met.no" in url]
    assert len(met_calls) == 1
    met_kwargs = next(kw for url, kw in session.calls if "met.no" in url)
    assert met_kwargs["headers"]["User-Agent"].startswith("OutbreakSentinel/")
    record = app_module._WEATHER_ATTEMPTS[CITY["name"]]
    assert record["ok"] is True
    assert record["provider"] == "met-norway"
    assert record["forecast_days"] == 2


def test_open_meteo_success_records_provider_open_meteo():
    session = _Session(lambda url, kwargs: _Response(payload=OPEN_METEO_PAYLOAD))
    result = _run(app_module.fetch_weather(session, CITY))

    assert result["provider"] == "open-meteo"
    assert len(result["forecast"]) == 2
    assert app_module._WEATHER_ATTEMPTS[CITY["name"]]["provider"] == "open-meteo"
    assert not any("met.no" in url for url, _ in session.calls)


def test_open_meteo_api_key_is_appended_when_set(monkeypatch):
    monkeypatch.setenv("OPEN_METEO_API_KEY", "test-key-123")
    session = _Session(lambda url, kwargs: _Response(payload=OPEN_METEO_PAYLOAD))
    _run(app_module.fetch_weather(session, CITY))

    params = session.calls[0][1]["params"]
    assert params["apikey"] == "test-key-123"


def test_stale_forecast_is_served_when_both_providers_fail(monkeypatch):
    app_module._WEATHER_LAST_GOOD[CITY["name"].lower()] = {
        "at": app_module.time.monotonic() - 600,
        "record": {
            "city": CITY["name"],
            "provider": "open-meteo",
            "forecast": [{"date": "2026-11-25", "temp_max": 22.0, "precipitation": 0.0}],
        },
    }

    def handler(url, kwargs):
        return _Response(status=429, payload={}, text="quota", headers={"Retry-After": "33545"})

    result = _run(app_module.fetch_weather(_Session(handler), CITY))

    assert result["stale"] is True
    assert result["provider"] == "open-meteo"
    assert result["forecast"][0]["date"] == "2026-11-25"
    assert result["stale_age_s"] >= 600
    record = app_module._WEATHER_ATTEMPTS[CITY["name"]]
    assert record["ok"] is True
    assert record["stale"] is True


def test_expired_stale_forecast_is_not_served():
    app_module._WEATHER_LAST_GOOD[CITY["name"].lower()] = {
        "at": app_module.time.monotonic() - app_module.WEATHER_STALE_MAX_S - 5,
        "record": {
            "city": CITY["name"],
            "provider": "open-meteo",
            "forecast": [{"date": "2026-11-20", "temp_max": 22.0}],
        },
    }

    def handler(url, kwargs):
        return _Response(status=500, payload={}, text="boom")

    result = _run(app_module.fetch_weather(_Session(handler), CITY))

    assert "error" in result
    assert result["provider"] == "none"
    assert "forecast" not in result
    assert app_module._WEATHER_ATTEMPTS[CITY["name"]]["ok"] is False
