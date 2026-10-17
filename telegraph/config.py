"""Configuration for the Telegraph buying layer.

Track 03 hard line: Chain ID, token address, price source, RPC URL and miner
selection are CONFIG VALUES, not code. Flipping to mainnet is a config change
(env vars or this module's defaults), not a code change.

Every value below is overridable via an environment variable of the same name
(upper-cased). Defaults point at Telegraph's live testnet (Base Sepolia).
"""
from __future__ import annotations

import os


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- Network / settlement (TESTNET by default) -------------------------------
TELEGRAPH_NODE_URL = _env("TELEGRAPH_NODE_URL", "https://devnode.telegraphprotocol.com")
TELEGRAPH_ENGINE_URL = _env("TELEGRAPH_ENGINE_URL", TELEGRAPH_NODE_URL.rstrip("/") + "/engine")
TELEGRAPH_CHAIN_ID = int(_env("TELEGRAPH_CHAIN_ID", "84532"))          # Base Sepolia
TELEGRAPH_CHAIN_CAIP = _env("TELEGRAPH_CHAIN_CAIP", "eip155:84532")
TELEGRAPH_NETWORK_LABEL = _env("TELEGRAPH_NETWORK_LABEL", "Base Sepolia (testnet)")
TELEGRAPH_USDC_ADDRESS = _env("TELEGRAPH_USDC_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e")
TELEGRAPH_RPC_URL = _env("TELEGRAPH_RPC_URL", "https://sepolia.base.org")
TELEGRAPH_EXPLORER_TX_URL = _env(
    "TELEGRAPH_EXPLORER_TX_URL", "https://sepolia.basescan.org/tx/{tx_hash}"
)

# --- Pricing -----------------------------------------------------------------
# Price source: the miner's declared floor price multiplied by the network
# demand multiplier, returned in the 402 challenge `amount` field. We never
# hardcode a price; we read it from the challenge / miner catalog.
TELEGRAPH_PRICE_SOURCE = _env(
    "TELEGRAPH_PRICE_SOURCE", "miner floor price x network demand multiplier (live, from 402 challenge)"
)

# --- Miner selection ---------------------------------------------------------
# "auto" lets the Engine's LLM router pick the best miner for the intent.
# Set to a numeric miner id to force a direct ask (POST /engine/v1/ask/{id}).
TELEGRAPH_MINER_SELECTION = _env("TELEGRAPH_MINER_SELECTION", "auto")

# --- Settlement mode ---------------------------------------------------------
# "mock"  -> Mechanism build: REST seam is real, settlement is mocked (no wallet).
# "live"  -> requires TELEGRAPH_EVM_PRIVATE_KEY and an x402 client; not available
#            in this environment (no x402 python SDK installed).
TELEGRAPH_SETTLEMENT_MODE = _env("TELEGRAPH_SETTLEMENT_MODE", "mock")
TELEGRAPH_EVM_PRIVATE_KEY = _env("TELEGRAPH_EVM_PRIVATE_KEY", "")

# Intent hint for discovery/routing. Empty -> Engine auto-classifies the query.
TELEGRAPH_INTENT_HINT = _env("TELEGRAPH_INTENT_HINT", "")

# Testnet boundary statement shown on screen, unprompted.
TESTNET_BOUNDARY = (
    "TESTNET ONLY — Base Sepolia (chain id 84532). No real value moves. "
    "Settlement is mocked (Mechanism build): the routing/discovery seam is real, "
    "the denomination is not. Flips to mainnet by changing TELEGRAPH_* config."
)


def is_live() -> bool:
    return TELEGRAPH_SETTLEMENT_MODE.lower() == "live" and bool(TELEGRAPH_EVM_PRIVATE_KEY)


TELEGRAPH_CONFIG = {
    "node_url": TELEGRAPH_NODE_URL,
    "engine_url": TELEGRAPH_ENGINE_URL,
    "chain_id": TELEGRAPH_CHAIN_ID,
    "chain_caip": TELEGRAPH_CHAIN_CAIP,
    "network_label": TELEGRAPH_NETWORK_LABEL,
    "usdc_address": TELEGRAPH_USDC_ADDRESS,
    "rpc_url": TELEGRAPH_RPC_URL,
    "explorer_tx_url": TELEGRAPH_EXPLORER_TX_URL,
    "price_source": TELEGRAPH_PRICE_SOURCE,
    "miner_selection": TELEGRAPH_MINER_SELECTION,
    "settlement_mode": TELEGRAPH_SETTLEMENT_MODE,
    "intent_hint": TELEGRAPH_INTENT_HINT,
    "testnet": True,
    "testnet_boundary": TESTNET_BOUNDARY,
}
