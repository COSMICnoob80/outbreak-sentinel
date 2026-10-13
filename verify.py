#!/usr/bin/env python3
"""Manually resolve a receipt after an official source confirms or refutes it.

Usage: python verify.py <receipt_id> CONFIRMED|REFUTED "<source citation>"
"""
import sys
from receipts import ReceiptStore

LEDGER = "history/receipts.jsonl"


def main(argv):
    if len(argv) != 4:
        print("usage: python verify.py <receipt_id> <CONFIRMED|REFUTED> <source>")
        return 2
    receipt_id, verdict, source = argv[1], argv[2].upper(), argv[3]
    if verdict not in ("CONFIRMED", "REFUTED"):
        print("verdict must be CONFIRMED or REFUTED")
        return 2
    store = ReceiptStore(LEDGER)
    store.resolve(receipt_id, verdict=verdict, source=source)
    print(f"resolved {receipt_id} as {verdict} — source: {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
