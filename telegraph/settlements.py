"""Append-only settlement ledger for the consumer surfaces.

Every assessment that runs through ``POST /telegraph/risk`` lands one JSONL row
here, whether it settled on-chain or degraded. The public ledger page and the
console telemetry line both read aggregates from this file — the same rows, so
the two surfaces can never disagree.

Same shape as ``receipts.py``: plain JSONL, one event per line, no rewriting.
If a line is unparseable it is skipped, never silently overwritten.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_PATH = os.path.join(_ROOT, "state", "settlements.jsonl")

PKT = timezone(timedelta(hours=5))


def pkt_stamp(epoch: int | None = None) -> str:
    """Human-readable Pakistan Standard Time stamp for a ledger row."""
    moment = datetime.fromtimestamp(epoch, PKT) if epoch is not None else datetime.now(PKT)
    return moment.strftime("%Y-%m-%d %H:%M PKT")


def record(entry: dict) -> dict:
    """Append one settlement row. Returns the row as written."""
    row = dict(entry)
    row.setdefault("ts", int(datetime.now(PKT).timestamp()))
    row.setdefault("time_pkt", pkt_stamp(row["ts"]))
    os.makedirs(os.path.dirname(os.path.abspath(LEDGER_PATH)), exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return row


def load(path: str | None = None) -> list[dict]:
    """Every ledger row, oldest first. Missing file is an empty ledger."""
    target = path or LEDGER_PATH
    if not os.path.exists(target):
        return []
    rows: list[dict] = []
    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def is_settled(row: dict) -> bool:
    """A row counts as on-chain only if it is live, not mocked, and carries a tx."""
    return bool(row.get("tx_hash")) and row.get("mode") == "live" and not row.get("mocked")


def aggregate(rows: list[dict]) -> dict:
    """KPI numbers for /telegraph/stats and the public ledger page."""
    settled = [r for r in rows if is_settled(r)]
    tx_hashes = {r["tx_hash"] for r in settled}
    total_usdc = round(sum(float(r.get("amount_usd") or 0) for r in settled), 4)

    verdicts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for row in rows:
        level = str(row.get("risk_level") or "").upper()
        if level in verdicts:
            verdicts[level] += 1

    integrity_pct = None
    if settled:
        integrity_pct = round(100.0 * len(tx_hashes) / len(settled), 1)

    last = settled[-1] if settled else None
    return {
        "assessments": len(rows),
        "settled": len(settled),
        "total_usdc": total_usdc,
        "integrity_pct": integrity_pct,
        "verdicts": verdicts,
        "last_settlement_pkt": (last or {}).get("time_pkt"),
    }
