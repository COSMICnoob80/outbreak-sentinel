"""Receipt ledger: immutable, append-only record of published risk calls."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any


def make_receipt(payload: dict) -> dict:
    """Build a receipt. receipt_id derives from the content hash, so identical
    inputs always produce the same id (idempotent re-publish)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    receipt = dict(payload)
    receipt["content_hash"] = f"sha256:{digest}"
    receipt["receipt_id"] = f"rcpt-{digest[:12]}"
    receipt["status"] = "OPEN"
    return receipt


class ReceiptStore:
    """Append-only JSONL ledger. Resolutions append a new event rather than
    mutating history, so the ledger itself stays auditable."""

    def __init__(self, path: str):
        self.path = str(path)
        self._receipts: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("_event") == "resolve":
                    rid = event["receipt_id"]
                    if rid in self._receipts:
                        self._receipts[rid]["status"] = "RESOLVED"
                        self._receipts[rid]["resolution"] = event["resolution"]
                else:
                    self._receipts[event["receipt_id"]] = event

    def append(self, receipt: dict) -> None:
        if receipt["receipt_id"] in self._receipts:
            return  # idempotent
        self._receipts[receipt["receipt_id"]] = receipt
        self._append_line(receipt)

    def resolve(self, receipt_id: str, verdict: str, source: str) -> None:
        if receipt_id not in self._receipts:
            raise KeyError(f"unknown receipt: {receipt_id}")
        self._receipts[receipt_id]["status"] = "RESOLVED"
        self._receipts[receipt_id]["resolution"] = {
            "verdict": verdict, "source": source
        }
        self._append_line({
            "_event": "resolve",
            "receipt_id": receipt_id,
            "resolution": {"verdict": verdict, "source": source},
        })

    def _append_line(self, obj: dict) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True) + "\n")

    def count(self) -> int:
        return len(self._receipts)

    def get(self, receipt_id: str) -> dict | None:
        return self._receipts.get(receipt_id)

    def all(self) -> list[dict]:
        return list(self._receipts.values())
