"""TelegraphClient — routes a paid intelligence request through Telegraph.

Real seam (documented REST API):
  - Discovery:  GET  {engine}/../api/miners?intent=...   (free)
  - Ask:        POST {engine}/v1/ask   body {"query":..., "context":...}
  - Challenge:  402 with PAYMENT-REQUIRED header (base64 JSON, accepts[])

Settlement:
  - mode="mock" (default): Mechanism build — routing/discovery real, settlement
    mocked. No wallet needed.
  - mode="live": requires TELEGRAPH_EVM_PRIVATE_KEY (funded Base Sepolia wallet)
    and the x402 Python SDK (x402[evm]). Signs an EIP-3009
    transferWithAuthorization and settles on Base Sepolia (chain 84532). The
    resulting tx hash comes from the server's PAYMENT-RESPONSE header.

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
    TELEGRAPH_EVM_PRIVATE_KEY,
    TELEGRAPH_EXPLORER_TX_URL,
    TELEGRAPH_INTENT_HINT,
    TELEGRAPH_MINER_SELECTION,
    TELEGRAPH_NETWORK_LABEL,
    TELEGRAPH_USDC_ADDRESS,
    is_live,
)

log = logging.getLogger(__name__)

# Optional x402 SDK (installed via x402[evm]). Guarded so the module still
# imports when the SDK is absent.
try:
    from eth_account import Account
    from x402 import x402Client
    from x402.http import x402HTTPClient
    from x402.mechanisms.evm.exact import ExactEvmScheme
    from x402.mechanisms.evm.signers import EthAccountSigner
    from x402.schemas import PaymentRequired

    _X402_AVAILABLE = True
except Exception as exc:  # pragma: no cover - defensive
    log.warning("x402 SDK not available: %s", exc)
    _X402_AVAILABLE = False

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

    async def _live_settle(
        self,
        query: str,
        context: dict | None,
        miner_id: str,
        miner_name: str,
        intent: str,
        challenge_info: dict[str, Any],
        real_challenge_received: bool,
    ) -> dict[str, Any]:
        """Live x402 settlement on Base Sepolia. Requires a funded wallet key."""
        if not _X402_AVAILABLE:
            raise RuntimeError("x402 SDK not installed")
        pk = TELEGRAPH_EVM_PRIVATE_KEY
        if not pk:
            raise RuntimeError("TELEGRAPH_EVM_PRIVATE_KEY missing")
        if not pk.startswith("0x"):
            pk = "0x" + pk
        account = Account.from_key(pk)
        signer = EthAccountSigner(account)

        x_client = x402Client()
        x_client.register("eip155:84532", ExactEvmScheme(signer))
        x_http = x402HTTPClient(x_client)

        # Prefer the Base Sepolia exact accept from the challenge.
        decoded = challenge_info.get("challenge")
        if not decoded:
            raise RuntimeError("no decoded payment challenge available")

        # The engine may offer accepts we cannot pay (e.g. an "escrow" entry that
        # omits the V2 schema's required `asset` / `maxTimeoutSeconds`). Only the
        # "exact" scheme is payable by ExactEvmScheme; keep the rest of the
        # challenge untouched and let model_validate() see exact-only accepts.
        accepts = decoded.get("accepts") or []
        exact_accepts = [a for a in accepts if isinstance(a, dict) and a.get("scheme") == "exact"]
        if not exact_accepts:
            schemes_seen = sorted({str(a.get("scheme")) for a in accepts if isinstance(a, dict)})
            raise RuntimeError(
                "no 'exact' scheme in x402 challenge accepts; schemes seen: "
                + (", ".join(schemes_seen) if schemes_seen else "<none>")
            )
        payable = dict(decoded)
        payable["accepts"] = exact_accepts
        payment_required = PaymentRequired.model_validate(payable)

        # Create the signed EIP-3009 payment payload.
        payload = await x_client.create_payment_payload(payment_required)

        # Encode into the PAYMENT-SIGNATURE header.
        headers = x_http.encode_payment_signature_header(payload)

        # Retry the ask with payment attached.
        url = TELEGRAPH_ENGINE_URL.rstrip("/") + "/v1/ask"
        body = {"query": query}
        if context:
            body["context"] = context
        status = None
        resp_body = None
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as r:
                status = r.status
                try:
                    resp_body = await r.json()
                except Exception:
                    resp_body = None
                normalized = {k.upper(): v for k, v in r.headers.items()}

                def get_header(name: str) -> str | None:
                    return normalized.get(name.upper())

                settle = None
                try:
                    settle = x_http.get_payment_settle_response(get_header)
                except Exception as exc:
                    log.warning("no settle response header: %s", exc)

        tx_hash = None
        payer = account.address
        network = None
        amount_uusdc = None
        settle_success = None
        if settle is not None:
            tx_hash = settle.transaction
            payer = settle.payer or payer
            network = settle.network
            amount_uusdc = settle.amount
            settle_success = settle.success

        # Amount: prefer real challenge amount, then settle amount, then default.
        amount_raw = challenge_info.get("amount")
        try:
            if amount_raw is not None:
                amount_usd = int(amount_raw) / 1_000_000
            elif amount_uusdc is not None:
                amount_usd = int(amount_uusdc) / 1_000_000
            else:
                amount_usd = 0.01
        except (TypeError, ValueError):
            amount_usd = 0.01

        ranked_answer = resp_body if isinstance(resp_body, dict) else {"raw": resp_body}

        proof = {
            "rail": "x402 (live)",
            "payer": payer,
            "miner": miner_id,
            "miner_name": miner_name,
            "intent": intent,
            "amount_uusdc": amount_uusdc or str(int(amount_usd * 1_000_000)),
            "amount_usd": round(amount_usd, 4),
            "epoch_id": 0,
            "settlement": "live (x402, Base Sepolia)",
            "chain": TELEGRAPH_CONFIG["chain_caip"],
            "chain_id": TELEGRAPH_CONFIG["chain_id"],
            "network_label": TELEGRAPH_NETWORK_LABEL,
            "tx_hash": tx_hash,
            "receipt_hash": "0x" + hashlib.sha256((query + str(tx_hash)).encode()).hexdigest(),
            "timestamp": int(time.time()),
            "real_challenge_received": real_challenge_received,
            "challenge_status": challenge_info.get("status"),
            "mode": "live",
            "mocked": False,
            "mock_note": None,
            "settle_success": settle_success,
            "settle_network": str(network) if network else None,
            "http_status": status,
        }
        proof["ranked_answer"] = ranked_answer
        self.last_proof = proof
        return {
            "mode": "live",
            "live": True,
            "ranked_answer": ranked_answer,
            "settlement": proof,
            "miner": miner_id,
            "miner_name": miner_name,
            "amount": amount_usd,
            "tx_hash": tx_hash,
            "network_label": TELEGRAPH_NETWORK_LABEL,
            "chain_id": TELEGRAPH_CONFIG["chain_id"],
            "real_challenge_received": real_challenge_received,
            "testnet_boundary": TELEGRAPH_CONFIG["testnet_boundary"],
        }

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

        # 5. LIVE settlement path (behind config flag). Only runs when a funded
        #    wallet key is present. Otherwise fall through to the mocked path.
        if is_live() and _X402_AVAILABLE:
            try:
                return await self._live_settle(
                    query, context, miner_id, miner_name, intent,
                    challenge_info, real_challenge_received,
                )
            except Exception as exc:
                log.exception("live settlement failed: %s", exc)
                # Fall through to mock? No — report the failure honestly.
                err_proof = {
                    "rail": "x402 (live, FAILED)",
                    "mode": "live",
                    "mocked": False,
                    "error": str(exc),
                    "miner": miner_id,
                    "miner_name": miner_name,
                    "amount_usd": amount_usd,
                    "tx_hash": None,
                    "real_challenge_received": real_challenge_received,
                    "timestamp": int(time.time()),
                }
                self.last_proof = err_proof
                return {
                    "mode": "live",
                    "live": False,
                    "error": str(exc),
                    "ranked_answer": None,
                    "settlement": err_proof,
                    "miner": miner_id,
                    "miner_name": miner_name,
                    "amount": amount_usd,
                    "tx_hash": None,
                    "network_label": TELEGRAPH_NETWORK_LABEL,
                    "chain_id": TELEGRAPH_CONFIG["chain_id"],
                    "real_challenge_received": real_challenge_received,
                    "testnet_boundary": TELEGRAPH_CONFIG["testnet_boundary"],
                }

        # 6. Settlement proof — MOCKED (Mechanism). Clearly marked.
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
                "Flips to live by setting TELEGRAPH_SETTLEMENT_MODE=live + a funded wallet key."
            ),
        }

        # 7. Ranked intelligence answer — in mock mode, synthesize a ranked answer
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