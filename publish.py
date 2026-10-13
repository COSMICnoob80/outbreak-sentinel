"""Turn HIGH/CRITICAL risk cards into durable receipts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from receipts import ReceiptStore, make_receipt

PKT = timezone(timedelta(hours=5))


def publish_cards(cards: list[dict], store: ReceiptStore,
                  city: str, disease: str) -> list[dict]:
    published = []
    for card in cards:
        if card.get("risk_level") not in ("HIGH", "CRITICAL"):
            continue
        receipt = make_receipt({
            "city": city,
            "disease": disease,
            "risk_level": card["risk_level"],
            "score": card["score"],
            "drivers": card["drivers"],
            "issued_at": datetime.now(PKT).isoformat(timespec="seconds"),
        })
        store.append(receipt)
        published.append(receipt)
    return published
