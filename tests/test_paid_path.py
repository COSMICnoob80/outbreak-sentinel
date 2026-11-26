"""W-8 gates: the paid path must never take money without a card.

The operator paid for Kabul/polio — a city outside the grid and a disease
outside the configured list — and got a settlement strip with no card. These
tests pin the structural fixes: the card is built before the purchase, a
missing card is a 400 that never calls the purchaser, on-demand cities are
adopted for one request without touching the grid, and every settlement is
appended to the runtime ledger (a log, not a deduped store).
"""
import pytest
from fastapi.testclient import TestClient

import app as app_module
from receipts import ReceiptStore
from telegraph import settlements

TX = "0x" + "e" * 64
ANSWER = "Kabul polio surveillance is being reinforced after new cases."

KABUL = {
    "name": "Kabul",
    "lat": 34.52813,
    "lon": 69.17233,
    "region": "global",
    "adopted": True,
}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    """No test writes the committed ledger or reuses another test's caches."""
    monkeypatch.setattr(settlements, "LEDGER_PATH", str(tmp_path / "settlements.jsonl"))
    monkeypatch.setattr(app_module, "STORE", ReceiptStore(str(tmp_path / "receipts.jsonl")))
    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setattr(app_module, "_ADOPTED_CITIES", {})
    monkeypatch.setattr(app_module, "_GEOCODE_CACHE", {})
    monkeypatch.setattr(app_module, "_ADOPTED_WEATHER_CACHE", {})
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")


class SettledClient:
    """TelegraphClient stand-in that settles without touching a network."""

    def __init__(self):
        self.last_proof = None
        self.calls = []

    async def buy_intelligence(self, query, context=None):
        self.calls.append({"query": query, "context": context})
        self.last_proof = {"tx_hash": TX, "amount_usd": 0.01}
        return {
            "mode": "live",
            "live": True,
            "ranked_answer": {"result": {"risk_assessment": ANSWER}},
            "miner": "9002",
            "miner_name": "txlens",
            "amount": 0.01,
            "tx_hash": TX,
            "network_label": "Base Sepolia (testnet)",
            "chain_id": 84532,
            "testnet_boundary": "TESTNET ONLY",
            "settlement": {
                "miner": "9002",
                "miner_name": "txlens",
                "amount_usd": 0.01,
                "amount_uusdc": "10000",
                "tx_hash": TX,
                "network_label": "Base Sepolia (testnet)",
                "chain_id": 84532,
                "rail": "x402 (live)",
                "receipt_hash": "0x" + "f" * 64,
                "real_challenge_received": True,
                "mocked": False,
            },
        }


def _weather(city="Karachi"):
    return [{
        "city": city,
        "provider": "open-meteo",
        "forecast": [{"date": "2026-11-27", "precipitation": 0.0, "temp_max": 24.0}],
    }]


def _karachi_news():
    return [{
        "title": "Karachi dengue cases rise - The Express Tribune",
        "link": "https://example.com/karachi-dengue",
        "outlet": "The Express Tribune",
        "published": "2026-11-25",
        "city": "Karachi",
    }]


async def _karachi_signals(disease="dengue"):
    return _karachi_news(), _weather(), [], 0.2


def _card(city="Karachi", disease="Dengue"):
    return {
        "city": city,
        "disease": disease,
        "risk_level": "LOW",
        "confidence": 0.4,
        "drivers": [{"kind": "model", "text": "no city-specific outbreak signal"}],
        "recommendation": "Monitor",
        "risk_score": 20,
        "sources": [],
        "vertical": "bio-surveillance",
    }


# ── 1. Card before purchase ───────────────────────────────────────────────

def test_card_is_built_before_the_purchase(monkeypatch):
    """Order is the guarantee: build → buy. A failed purchase still returns a card."""
    order = []

    def fake_build(news, weather, social, sent, disease, city=None, extra_cities=None):
        order.append("build")
        return [_card()], "deterministic"

    class FailingClient:
        last_proof = None

        async def buy_intelligence(self, query, context=None):
            order.append("buy")
            raise RuntimeError("facilitator unreachable")

    monkeypatch.setattr(app_module, "_telegraph_client", FailingClient())
    monkeypatch.setattr(app_module, "collect_signals", _karachi_signals)
    monkeypatch.setattr(app_module, "_build_deterministic_cards", fake_build)

    resp = TestClient(app_module.app).post("/telegraph/risk", json={
        "query": "Is dengue exploding in Karachi?",
        "city": "Karachi",
        "disease": "dengue",
    })

    assert resp.status_code == 200
    assert order == ["build", "buy"], "the card must be built before money moves"
    body = resp.json()
    assert body["settlement_error"] and "facilitator unreachable" in body["settlement_error"]
    assert body["risk_card"]["city"] == "Karachi", "a card must survive a failed purchase"


# ── 2. No card → 400, purchaser never called ──────────────────────────────

class CountingClient:
    last_proof = None

    def __init__(self):
        self.calls = 0

    async def buy_intelligence(self, query, context=None):
        self.calls += 1
        return {}


@pytest.mark.parametrize("city", ["", "   ", "zzzz-not-a-real-city"])
def test_no_card_returns_400_and_never_purchases(monkeypatch, city):
    async def unresolved(name):
        return None  # what a geocoder miss looks like

    monkeypatch.setattr(app_module, "_adopt_city", unresolved)
    client = CountingClient()
    monkeypatch.setattr(app_module, "_telegraph_client", client)

    resp = TestClient(app_module.app).post("/telegraph/risk", json={
        "query": "Assess risk", "city": city, "disease": "dengue",
    })

    assert resp.status_code == 400
    assert client.calls == 0, "money must never leave the wallet without a card"
    assert "purchased" in resp.json()["detail"].lower()


# ── 3. Settlement append (a log: no dedupe) ───────────────────────────────

def test_each_settled_request_appends_exactly_one_row(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "_telegraph_client", SettledClient())
    monkeypatch.setattr(app_module, "collect_signals", _karachi_signals)

    client = TestClient(app_module.app)
    payload = {"query": "Karachi check", "city": "Karachi", "disease": "dengue"}

    assert client.post("/telegraph/risk", json=payload).status_code == 200
    rows = settlements.load(str(tmp_path / "settlements.jsonl"))
    assert len(rows) == 1
    assert rows[0]["tx_hash"] == TX
    assert rows[0]["city"] == "Karachi"

    # Same request again: the ledger is a log, so it appends a second row.
    assert client.post("/telegraph/risk", json=payload).status_code == 200
    rows = settlements.load(str(tmp_path / "settlements.jsonl"))
    assert len(rows) == 2
    assert [r["tx_hash"] for r in rows] == [TX, TX]


# ── 4. Ad-hoc city + ad-hoc disease, gate intact ──────────────────────────

def test_adopts_city_and_disease_for_the_paid_path_without_touching_the_grid(monkeypatch):
    kabul_news = [
        {  # city + disease match — the only evidence
            "title": "Kabul polio vaccination drive reaches districts - Dawn",
            "link": "https://example.com/kabul-polio",
            "outlet": "Dawn",
            "published": "2026-11-24",
            "city": "Kabul",
        },
        {  # right city, wrong disease — the disease-term gate must drop it
            "title": "Kabul measles cases reported in camps - Dawn",
            "link": "https://example.com/kabul-measles",
            "outlet": "Dawn",
            "published": "2026-11-24",
            "city": "Kabul",
        },
        {  # right city, no disease at all — not evidence
            "title": "Kabul cricket team wins regional final - ESPN",
            "link": "https://example.com/kabul-cricket",
            "outlet": "ESPN",
            "published": "2026-11-24",
            "city": "Kabul",
        },
    ]

    async def adopt(name):
        return KABUL

    async def signals(city, disease):
        return kabul_news, [{
            "city": "Kabul",
            "provider": "open-meteo",
            "forecast": [{"date": "2026-11-27", "precipitation": 1.0, "temp_max": 18.0}],
        }]

    monkeypatch.setattr(app_module, "_adopt_city", adopt)
    monkeypatch.setattr(app_module, "_adopt_signals", signals)
    monkeypatch.setattr(app_module, "_telegraph_client", SettledClient())

    grid_before = [c["name"] for c in app_module.CONFIG["cities"]]
    body = TestClient(app_module.app).post("/telegraph/risk", json={
        "query": "Polio risk in Kabul?", "city": "Kabul", "disease": "polio",
    }).json()

    card = body["risk_card"]
    assert body["city_adopted"] is True
    assert card["city"] == "Kabul"
    assert card["disease"] == "Polio"
    assert [s["title"] for s in card["sources"]] == [kabul_news[0]["title"]]
    assert card["evidence_count"] == 1

    # The ad-hoc city never enters the standing grid.
    assert [c["name"] for c in app_module.CONFIG["cities"]] == grid_before
    assert "Kabul" not in grid_before
