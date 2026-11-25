"""W-3 acceptance gates: paid intelligence drives the card, receipts are real,
and settlement proof survives a restart.

Each test isolates its ledgers so nothing is written to the committed files.
"""
import json

import pytest
from fastapi.testclient import TestClient

import app as app_module
from receipts import ReceiptStore
from telegraph import settlements

TX = "0x" + "c" * 64
ANSWER = "Karachi dengue admissions are rising faster than the 5-year seasonal mean."


@pytest.fixture(autouse=True)
def _isolated_settlement_ledger(monkeypatch, tmp_path):
    """Keep /telegraph/risk writes out of the committed state/settlements.jsonl."""
    monkeypatch.setattr(settlements, "LEDGER_PATH", str(tmp_path / "settlements.jsonl"))


class PaidClient:
    """TelegraphClient stand-in that returns a usable ranked answer."""

    def __init__(self, answer):
        self.answer = answer
        self.last_proof = None

    async def buy_intelligence(self, query, context=None):
        ranked = {"result": {"risk_assessment": self.answer}} if self.answer else {}
        self.last_proof = {
            "payer": "0xMOCK_PAYER_NOT_A_REAL_WALLET",
            "tx_hash": TX,
            "amount_usd": 0.01,
            "ranked_answer": ranked,
        }
        return {
            "mode": "live",
            "live": True,
            "ranked_answer": ranked,
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
                "receipt_hash": "0x" + "d" * 64,
                "real_challenge_received": True,
                "mocked": False,
            },
        }


async def _signals(disease="dengue"):
    return [], [], [], 0.0


def _high_card(news, weather, social, sent, disease, city=None):
    return ([{
        "city": "Karachi",
        "disease": "Dengue",
        "risk_level": "HIGH",
        "confidence": 0.8,
        "drivers": [{"kind": "news", "text": "6 city-specific dengue reports in 7 days"}],
        "recommendation": "Monitor admissions",
        "risk_score": 65,
        "sources": [{"title": "Karachi dengue cases rise", "url": "https://example.com/a"}],
        "vertical": "bio-surveillance",
    }], "deterministic")


def test_paid_answer_becomes_a_cited_telegraph_driver(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "_telegraph_client", PaidClient(ANSWER))
    monkeypatch.setattr(app_module, "collect_signals", _signals)
    monkeypatch.setattr(app_module, "_build_deterministic_cards", _high_card)
    monkeypatch.setattr(app_module, "STORE", ReceiptStore(str(tmp_path / "receipts.jsonl")))
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")

    body = TestClient(app_module.app).post("/telegraph/risk", json={
        "query": "Is dengue exploding in Karachi?",
        "city": "Karachi",
        "disease": "dengue",
    }).json()

    paid = body["paid_intelligence"]
    assert paid["status"] == "used"
    assert paid["miner"] == "txlens"
    assert paid["driver"] and "txlens" in paid["driver"] and "0.01" in paid["driver"]

    drivers = body["risk_card"]["drivers"]
    assert drivers[0]["kind"] == "telegraph"
    assert "telegraph" in app_module.ALLOWED_DRIVER_KINDS
    assert ANSWER in drivers[0]["text"]


def test_empty_ranked_answer_is_reported_never_faked(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "_telegraph_client", PaidClient(""))
    monkeypatch.setattr(app_module, "collect_signals", _signals)
    monkeypatch.setattr(app_module, "_build_deterministic_cards", _high_card)
    monkeypatch.setattr(app_module, "STORE", ReceiptStore(str(tmp_path / "receipts.jsonl")))
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")

    body = TestClient(app_module.app).post("/telegraph/risk", json={
        "query": "Is dengue exploding in Karachi?",
        "city": "Karachi",
        "disease": "dengue",
    }).json()

    paid = body["paid_intelligence"]
    assert paid["status"] == "unavailable"
    assert paid["reason"]
    assert paid["driver"] is None
    assert all(d["kind"] != "telegraph" for d in body["risk_card"]["drivers"])


def test_status_seeds_last_settlement_from_ledger(monkeypatch, tmp_path):
    ledger = tmp_path / "settlements.jsonl"
    ledger.write_text(json.dumps({
        "city": "Karachi", "disease": "dengue", "risk_level": "HIGH",
        "tx_hash": TX, "mode": "live", "mocked": False,
        "amount_usd": 0.01, "amount_uusdc": "10000",
        "miner": "9002", "miner_name": "txlens",
        "time_pkt": "2026-11-16 20:02 PKT",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(settlements, "LEDGER_PATH", str(ledger))
    monkeypatch.setattr(app_module._telegraph_client, "last_proof", None)

    status = TestClient(app_module.app).get("/telegraph/status").json()

    assert status["last_settlement_source"] == "ledger"
    seeded = status["last_settlement"]
    assert seeded["tx_hash"] == TX
    assert seeded["settlement"]["tx_hash"] == TX
    assert seeded["settlement"]["mocked"] is False
    assert seeded["explorer_tx_url"].endswith(TX)


def test_high_card_finalizes_into_a_receipt(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "_telegraph_client", PaidClient(ANSWER))
    monkeypatch.setattr(app_module, "collect_signals", _signals)
    monkeypatch.setattr(app_module, "_build_deterministic_cards", _high_card)
    monkeypatch.setattr(app_module, "STORE", ReceiptStore(str(tmp_path / "receipts.jsonl")))
    monkeypatch.setattr(app_module, "_RISK_CACHE", {})
    monkeypatch.setenv("SENTINEL_NARRATOR", "0")

    client = TestClient(app_module.app)
    body = client.get("/risk", params={"disease": "dengue", "refresh": 1}).json()

    assert body["receipts"], "a finalized HIGH card must file a receipt"
    receipt = app_module.STORE.get(body["receipts"][0])
    assert receipt["risk_level"] == "HIGH"
    assert receipt["score"] == 65
    assert receipt["status"] == "OPEN"
    assert receipt["drivers"] == ["6 city-specific dengue reports in 7 days"]

    board = client.get("/scoreboard").json()
    assert board["total_receipts"] == 1

    # A second identical build must not duplicate the claim.
    client.get("/risk", params={"disease": "dengue", "refresh": 1})
    assert client.get("/scoreboard").json()["total_receipts"] == 1
