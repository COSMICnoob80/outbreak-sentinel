"""Turn HIGH/CRITICAL risk cards into durable receipts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from receipts import ReceiptStore, make_receipt

PKT = timezone(timedelta(hours=5))


def _driver_text(driver) -> str:
    """Plain text from either driver shape (object or legacy string)."""
    if isinstance(driver, dict):
        return str(driver.get("text") or "").strip()
    return str(driver or "").strip()


def publish_cards(cards: list[dict], store: ReceiptStore,
                  city: str | None = None, disease: str | None = None) -> list[dict]:
    """File one receipt per HIGH/CRITICAL card; return every receipt filed.

    The receipt id is the hash of the *claim* (city, subject, level, score,
    drivers, vertical), not of the moment it was filed — so rebuilding the same
    grid cannot append the same call twice. ``issued_at`` is stamped onto the
    receipt after hashing: it records first filing without changing identity.
    """
    published = []
    for card in cards or []:
        if not isinstance(card, dict):
            continue
        if card.get("risk_level") not in ("HIGH", "CRITICAL"):
            continue
        claim = {
            "city": card.get("city") or city,
            "disease": card.get("disease") if card.get("disease") is not None else disease,
            "risk_level": card["risk_level"],
            "score": card.get("risk_score", card.get("score", 0)),
            "drivers": [t for t in (_driver_text(d) for d in card.get("drivers") or []) if t],
            "vertical": card.get("vertical"),
        }
        receipt = make_receipt(claim)
        existing = store.get(receipt["receipt_id"])
        if existing:
            published.append(existing)
            continue
        receipt["issued_at"] = datetime.now(PKT).isoformat(timespec="seconds")
        store.append(receipt)
        published.append(receipt)
    return published
