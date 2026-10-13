import pytest
from receipts import ReceiptStore, make_receipt

def test_make_receipt_is_deterministic(tmp_path):
    payload = {
        "city": "Karachi", "disease": "dengue", "risk_level": "HIGH",
        "score": 62, "drivers": ["News uptick: 14 articles in 24h"],
        "issued_at": "2026-11-02T09:15:00+05:00",
    }
    r = make_receipt(payload)
    assert r["receipt_id"]
    assert r["content_hash"].startswith("sha256:")
    assert make_receipt(payload)["content_hash"] == r["content_hash"]

def test_store_roundtrip_and_append_only(tmp_path):
    store = ReceiptStore(tmp_path / "ledger.jsonl")
    r1 = make_receipt({"city": "Karachi", "disease": "dengue",
                       "risk_level": "HIGH", "score": 62, "drivers": [],
                       "issued_at": "2026-11-02T09:15:00+05:00"})
    store.append(r1)
    assert store.count() == 1
    assert store.get(r1["receipt_id"]) == r1
    store.resolve(r1["receipt_id"], verdict="CONFIRMED",
                  source="DGHS Pakistan weekly bulletin 2026-11-07")
    after = store.get(r1["receipt_id"])
    assert after["status"] == "RESOLVED"
    assert after["resolution"]["verdict"] == "CONFIRMED"
    assert after["content_hash"] == r1["content_hash"]
    assert store.count() == 1

def test_store_survives_reload(tmp_path):
    store = ReceiptStore(tmp_path / "ledger.jsonl")
    r = make_receipt({"city": "Lahore", "disease": "cholera",
                      "risk_level": "CRITICAL", "score": 78, "drivers": [],
                      "issued_at": "2026-11-03T08:00:00+05:00"})
    store.append(r)
    reopened = ReceiptStore(tmp_path / "ledger.jsonl")
    assert reopened.count() == 1
    assert reopened.get(r["receipt_id"])["city"] == "Lahore"
