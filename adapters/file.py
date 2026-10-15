"""File channel — appends the card as one JSON line.

Append-only, mirroring the receipt ledger's honesty guarantees: alerts are
never rewritten in place, only added. Path comes from SENTINEL_ALERT_FILE
(default: history/alerts.jsonl).
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .base import Channel

log = logging.getLogger(__name__)

DEFAULT_ALERT_FILE = "history/alerts.jsonl"


class FileChannel(Channel):
    name = "file"

    def __init__(self, path: str | None = None):
        target = path or os.environ.get("SENTINEL_ALERT_FILE") or DEFAULT_ALERT_FILE
        self.path = Path(target)

    async def send(self, card: dict) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(card, sort_keys=True) + "\n")
            return True
        except Exception as exc:
            log.warning("file: append to %s failed: %s", self.path, exc)
            return False
