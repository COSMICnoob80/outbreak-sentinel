"""Turn HIGH/CRITICAL risk cards into durable receipts."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from receipts import ReceiptStore, make_receipt

PKT = timezone(timedelta(hours=5))


def _driver_text(driver) -> str:
    """Plain text from either driver shape (object or legacy string)."""
    if isinstance(driver, dict):
        return str(driver.get("text") or "").strip()
    return str(driver or "").strip()


def _claim_identity(card: dict, city: str | None, disease: str | None) -> dict:
    """Stable identity for one claim: city + vertical + disease + day window.

    Deliberately excludes the driver text and score. Those move when a render
    happens to see one more report, which is exactly how one event used to file
    two receipts. The day bucket lets an event that is still running file a
    fresh claim on a later day without duplicating today's.
    """
    return {
        "city": str(card.get("city") or city or "").strip().lower(),
        "vertical": str(card.get("vertical") or "bio-surveillance").strip().lower(),
        "disease": str(card.get("disease") or disease or "").strip().lower(),
        "window": datetime.now(PKT).strftime("%Y-%m-%d"),
    }


def _identity_digest(identity: dict) -> str:
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def publish_cards(cards: list[dict], store: ReceiptStore,
                  city: str | None = None, disease: str | None = None) -> list[dict]:
    """File one receipt per HIGH/CRITICAL card; return every receipt filed.

    The receipt id is the hash of the *stable claim identity* (city, vertical,
    disease, day window), not of the moment it was filed or of its volatile
    drivers/score — so re-emitting the same card, even with a different report
    count, returns the receipt already on file and never appends a second one.
    ``issued_at`` records first filing and does not affect identity. The stored
    receipt keeps the same fields it always has; only the id/hash derivation
    changed.
    """
    published = []
    for card in cards or []:
        if not isinstance(card, dict):
            continue
        if card.get("risk_level") not in ("HIGH", "CRITICAL"):
            continue
        identity = _claim_identity(card, city, disease)
        digest = _identity_digest(identity)
        receipt_id = f"rcpt-{digest[:12]}"
        existing = store.get(receipt_id)
        if existing:
            published.append(existing)
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
        # The stable identity names the claim; the payload above is its record.
        receipt["receipt_id"] = receipt_id
        receipt["content_hash"] = f"sha256:{digest}"
        receipt["issued_at"] = datetime.now(PKT).isoformat(timespec="seconds")
        store.append(receipt)
        published.append(receipt)
    return published
