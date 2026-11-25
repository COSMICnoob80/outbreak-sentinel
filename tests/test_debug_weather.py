"""`/debug/weather` surfaces the real last attempt — and never 500s."""
from fastapi.testclient import TestClient

import app as app_module


def _client():
    return TestClient(app_module.app)


def test_fresh_boot_reports_no_attempt(monkeypatch):
    monkeypatch.setattr(app_module, "_WEATHER_ATTEMPTS", {})
    body = _client().get("/debug/weather").json()
    assert body["note"] == "no weather attempt yet"
    assert body["cities"] == []
    assert body["configured_cities"] >= 1


def test_failed_attempt_surfaces_raw_error_and_status(monkeypatch):
    monkeypatch.setattr(app_module, "_WEATHER_ATTEMPTS", {})
    name = app_module.CONFIG["cities"][0]["name"]
    app_module._record_weather_attempt(
        name, ok=False, http_status=403, error="HTTP 403",
    )
    body = _client().get("/debug/weather").json()
    assert body["failed"] == 1
    row = next(r for r in body["cities"] if r["city"] == name)
    assert row["http_status"] == 403
    assert row["error"] == "HTTP 403"
    assert row["ok"] is False
    assert row["attempts"] == 1


def test_endpoint_never_500s_on_internal_failure(monkeypatch):
    def boom():
        raise RuntimeError("cache exploded")

    monkeypatch.setattr(app_module, "weather_cache_state", boom)
    resp = _client().get("/debug/weather")
    assert resp.status_code == 200
    assert "cache exploded" in resp.json()["error"]
