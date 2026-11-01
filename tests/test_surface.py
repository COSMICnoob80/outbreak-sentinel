"""Consumer surfaces: page routes and the settlement ledger write path."""
import app as app_module
from fastapi.testclient import TestClient
from telegraph import settlements

TX = "0x" + "a" * 64


class FakeClient:
    """Stand-in for TelegraphClient — no network, no testnet spend."""

    last_proof = None

    async def buy_intelligence(self, query, context=None):
        self.last_proof = {
            "payer": "0xMOCK_PAYER_NOT_A_REAL_WALLET",
            "tx_hash": TX,
            "amount_usd": 0.01,
        }
        return {
            "mode": "live",
            "live": True,
            "ranked_answer": {"source": "telegraph (test stub)"},
            "miner": "9002",
            "miner_name": "txlens",
            "amount": 0.01,
            "tx_hash": TX,
            "network_label": "Base Sepolia (testnet)",
            "chain_id": 84532,
            "real_challenge_received": True,
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
                "receipt_hash": "0x" + "b" * 64,
                "real_challenge_received": True,
                "mocked": False,
            },
        }


async def _fake_collect_signals():
    return [], [], [], 0.0


async def _fake_fuse(news, weather, social, sent, disease, city=None):
    return ([{
        "city": "Karachi",
        "disease": disease,
        "risk_level": "HIGH",
        "confidence": 0.71,
        "drivers": ["News uptick: 14 articles in 24h", "Heavy rain forecast: 61.0mm",
                    "High panic sentiment: 0.81", "Extra driver"],
        "recommendation": "Investigate signals",
        "summary": "Dengue is escalating in Karachi. Second sentence is not the verdict.",
        "sources": [{"title": "Karachi dengue cases rise", "url": "https://example.com/a"}],
        "chart": [],
        "illustration_hint": "dengue-rain-high",
    }], "llm")


def test_surface_pages_return_200():
    client = TestClient(app_module.app)

    assess = client.get("/telegraph/assess")
    assert assess.status_code == 200
    assert "text/html" in assess.headers["content-type"]
    assert "One assessment. Real sources. A receipt nobody can change." in assess.text

    ledger = client.get("/telegraph/ledger")
    assert ledger.status_code == 200
    assert "text/html" in ledger.headers["content-type"]
    assert "No settlements yet" in ledger.text


def test_settlement_writes_one_ledger_row(tmp_path, monkeypatch):
    ledger_path = tmp_path / "settlements.jsonl"
    monkeypatch.setattr(settlements, "LEDGER_PATH", str(ledger_path))
    monkeypatch.setattr(app_module, "_telegraph_client", FakeClient())
    monkeypatch.setattr(app_module, "collect_signals", _fake_collect_signals)
    monkeypatch.setattr(app_module, "_fuse_or_rule_based", _fake_fuse)

    client = TestClient(app_module.app)
    resp = client.post("/telegraph/risk", json={
        "query": "Is dengue exploding in Karachi right now?",
        "city": "Karachi",
        "disease": "dengue",
        "amount_uusdc": 10000,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["spend_tier"] == "essentials"
    assert body["amount_uusdc_requested"] == 10000
    assert body["tx_hash"] == TX

    rows = settlements.load(str(ledger_path))
    assert len(rows) == 1
    row = rows[0]
    assert row["city"] == "Karachi"
    assert row["disease"] == "dengue"
    assert row["risk_level"] == "HIGH"
    assert row["verdict"] == "Dengue is escalating in Karachi."
    assert row["tx_hash"] == TX
    assert row["mode"] == "live"
    assert row["mocked"] is False
    assert row["spend_tier"] == "essentials"
    assert row["amount_uusdc_requested"] == "10000"
    assert len(row["drivers"]) == 3
    assert row["sources_count"] == 1
    assert row["time_pkt"].endswith("PKT")

    stats = client.get("/telegraph/stats")
    assert stats.status_code == 200
    payload = stats.json()
    assert payload["assessments"] == 1
    assert payload["settled"] == 1
    assert payload["total_usdc"] == 0.01
    assert payload["verdicts"]["HIGH"] == 1
    assert len(payload["settlements"]) == 1
