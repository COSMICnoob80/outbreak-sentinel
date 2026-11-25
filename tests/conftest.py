"""Test isolation: the suite never calls a live LLM and never writes the repo ledger."""
import os
import tempfile

os.environ["SENTINEL_NARRATOR"] = "0"
# app.py resolves its receipt ledger path at import time. Point it at a throwaway
# directory so a test that exercises /risk cannot append to history/receipts.jsonl.
os.environ.setdefault(
    "SENTINEL_RECEIPTS_PATH",
    os.path.join(tempfile.mkdtemp(prefix="sentinel-tests-"), "receipts.jsonl"),
)
