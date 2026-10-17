"""TelegraphClient — routes a paid intelligence request through Telegraph.

Real seam (documented REST API):
  - Discovery:  GET  {engine}/../api/miners?intent=...   (free)
  - Ask:        POST {engine}/v1/ask   body {"query":..., "context":...}
  - Challenge:  402 with PAYMENT-REQUIRED header (base64 JSON, accepts[])

Settlement (x402 payment) is MOCKED in this environment because no x402
Python SDK / wallet is available. This is Telegraph's "Mechanism" scenario:
routing + discovery are real; the denomination is not. The mock is clearly
marked in every returned proof (mode="mocked", real_challenge_received flag).

Real vs mocked is stated plainly in is_live() / status endpoints.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
import uuid
from typing import Any

import aiohttp

from .config import (
    TELEGRAPH_CONFIG,
    TELEGRAPH_ENGINE_URL,
    TELEGRAPH_EXPLORER_TX_URL,
    TELEGRAPH_INTENT_HINT,
    TELEGRAPH_MINER_SELECTION,
    TELEGRAPH_NETWORK_LABEL,
    TELEGRAPH_USDC_ADDRESS,
    is_live,
)

log = logging.getLogger(__name__)

# Intent used for discovery when auto-routing. Picked for outbreak-risk relevance.
DEFAULT_DISCOVERY_INTENT = "SENTIMENT_ANALYSIS"


class TelegraphClient:
    def __init__(self) -> None:
        self.last_proof: dict[str, Any] | None = None

    async def _discover_miner(self, intent: str) -> dict[str, Any] | None:
        """Free discovery endpoint — real call to the live node."""
        url = TELEGRAPH_ENGINE_URL.replace("/engine", "") + "/api/miners"
        params = {"intent": intent, "limit": "5"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()
                    if isinstance(data, list) and data:
                        return data[0]
                    if isinstance(data, dict):
                        for key in ("miners", "data", "results"):
                            if isinstance(data.get(key), list) and data[key]:
                                return data[key][0]
        except Exception as exc:  # network failure -> offline seam
            log.warning("telegraph discovery failed: %s", exc)
        return None

    async def _real_challenge(self, query: str, context: dict | None) -> dict[str, Any]:
        """Issue the real POST /engine/v1/ask and capture the 402 challenge.

        Returns a dict with `status`, `challenge` (parsed accepts), `raw_headers`.
        Does NOT pay. The node returns 402 for unpaid requests.
        """
        url = TELEGRAPH_ENGINE_URL.rstrip("/") + "/v1/ask"
        body = {"query": query}
        if context:
            body["context"] = context
        out: dict[str, Any] = {"status": None, "challenge": None, "accepts": [], "pay_to": None, "amount": None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=20)) as r:
                    out["status"] = r.status
                    # Capture PAYMENT-REQUIRED header (base64 JSON)
                    pr = r.headers.get("PAYMENT-REQUIRED") or r.headers.get("payment-required")
                    if pr:
                        try:
                            decoded = base64.b64decode(pr)
                            challenge = json.loads(decoded)
                            out["challenge"] = challenge
                            accepts = challenge.get("accepts") or []
                            out["accepts"] = accepts
                            if accepts:
                                a = accepts[0]
                                out["amount"] = a.get("amount")
                                out["pay_to"] = a.get("payTo")
                                out["network"] = a.get("network")
                                out["asset"] = a.get("asset")
                        except Exception as exc:
                            log.warning("could not decode payment challenge: %s", exc)
                    # Also read body (short summary) for humans
                    try:
                        out["body"] = await r.json()
                    except Exception:
                        out["body"] = None
        except Exception as exc:
            log.warning("telegraph ask request failed: %s", exc)
            out["error"] = str(exc)
        return out

    async def buy_intelligence(self, query: str, context: dict | None = None) -> dict[str, Any]:
        """Route a paid intelligence request through Telegraph.

        Returns a dict with:
          - mode: "live" or "mocked"
          - ranked_answer: the verified ranked intelligence answer
          - settlement: {miner_id, miner_name, amount, tx_hash, network_label, ...}
          - real_challenge_received: whether a real 402 challenge was obtained
          - testnet_boundary: statement
        """
        # 1. Real discovery (free) — get a real miner candidate for the proof.
        intent = TELEGRAPH_INTENT_HINT or DEFAULT_DISCOVERY_INTENT
        miner = await self._discover_miner(intent)

        # 2. Real seam: issue the ask, capture the 402 challenge (no payment).
        challenge_info = await self._real_challenge(query, context)
        real_challenge_received = challenge_info.get("status") == 402 and bool(challenge_info.get("accepts"))

        # 3. Miner selection for the proof.
        if TELEGRAPH_MINER_SELECTION and TELEGRAPH_MINER_SELECTION.lower() != "auto":
            miner_id = TELEGRAPH_MINER_SELECTION
            miner_name = f"miner-{miner_id}"
        elif miner:
            miner_id = str(miner.get("id") or miner.get("miner_id") or "unknown")
            miner_name = miner.get("slug") or miner.get("name") or miner.get("miner_name") or f"miner-{miner_id}"
            intent = miner.get("supported_intents", [intent])[0] if miner.get("supported_intents") else intent
        else:
            miner_id = "unknown"
            miner_name = "unknown-miner"

        # 4. Amount: prefer the real challenge amount, else a documented default ($0.01).
        amount_raw = challenge_info.get("amount")
        try:
            amount_usd = (int(amount_raw) / 1_000_000) if amount_raw is not None else 0.01
        except (TypeError, ValueError):
            amount_usd = 0.01

        # 5. Settlement proof — MOCKED (Mechanism). Clearly marked.
        # tx_hash is synthetic but well-formed; labeled as mock so no one mistakes it.
        seed = f"{query}|{miner_id}|{time.time()}|MOCK"
        mock_tx_hash = "0x" + hashlib.sha256(seed.encode()).hexdigest()
        proof = {
            "rail": "x402 (mocked)",
            "payer": "0xMOCK_PAYER_NOT_A_REAL_WALLET",
            "miner": miner_id,
            "miner_name": miner_name,
            "intent": intent,
            "amount_uusdc": str(int(amount_usd * 1_000_000)),
            "amount_usd": round(amount_usd, 4),
            "epoch_id": 0,
            "settlement": "mocked (Mechanism)",
            "chain": TELEGRAPH_CONFIG["chain_caip"],
            "chain_id": TELEGRAPH_CONFIG["chain_id"],
            "network_label": TELEGRAPH_NETWORK_LABEL,
            "tx_hash": mock_tx_hash,
            "receipt_hash": "0x" + hashlib.sha256((query + mock_tx_hash).encode()).hexdigest(),
            "timestamp": int(time.time()),
            "real_challenge_received": real_challenge_received,
            "challenge_status": challenge_info.get("status"),
            "mode": "mocked",
            "mocked": True,
            "mock_note": (
                "SETTLEMENT IS MOCKED. This is a Mechanism build: the REST/discovery "
                "seam is real (a real 402 challenge was " + ("received" if real_challenge_received else "NOT received") +
                "), but no payment was made and tx_hash is synthetic. "
                "Flips to live by setting TELEGRAPH_SETTLEMENT_MODE=live + a wallet."
            ),
        }

        # 6. Ranked intelligence answer — in mock mode, synthesize a ranked answer
        # shaped like a Telegraph miner response, clearly marked as mock.
        ranked_answer = {
            "source": "telegraph (mocked)",
            "miner_id": miner_id,
            "miner_name": miner_name,
            "intent": intent,
            "result": {
                "risk_assessment": (
                    "Mocked ranked intelligence: elevated outbreak risk signal fused from "
                    "news + weather + sentiment (Telegraph miner would return verified, "
                    "ranked answer here)."
                ),
                "confidence": 0.72,
                "drivers": [
                    "Telegraph-ranked miner output (mocked)",
                    "Discovery hit: " + ("real miner " + miner_name if miner else "no miner discovered"),
                ],
            },
            "cost_usd": amount_usd,
            "duration_ms": 0,
            "signal_hash": proof["receipt_hash"],
            "mocked": True,
        }

        proof["ranked_answer"] = ranked_answer
        self.last_proof = proof
        return {
            "mode": "mocked",
            "live": False,
            "ranked_answer": ranked_answer,
            "settlement": proof,
            "miner": miner_id,
            "miner_name": miner_name,
            "amount": amount_usd,
            "tx_hash": mock_tx_hash,
            "network_label": TELEGRAPH_NETWORK_LABEL,
            "chain_id": TELEGRAPH_CONFIG["chain_id"],
            "real_challenge_received": real_challenge_received,
            "testnet_boundary": TELEGRAPH_CONFIG["testnet_boundary"],
        }

    # Alias for clarity
    async def route_paid_request(self, query: str, context: dict | None = None) -> dict[str, Any]:
        return await self.buy_intelligence(query, context)
