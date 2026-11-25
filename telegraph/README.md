# Telegraph buying layer (Track 01 — Apps & Agents)

Outbreak Sentinel buys ranked intelligence through Telegraph instead of calling
APIs directly. This package is the client.

## What is real vs mocked

- REAL: HTTP seam against Telegraph's documented REST API.
  - Discovery: `GET https://devnode.telegraphprotocol.com/api/miners?intent=...`
  - Ask: `POST https://devnode.telegraphprotocol.com/engine/v1/ask` (body `{"query":...}`)
  - The 402 challenge is actually requested and its `PAYMENT-REQUIRED` header
    is decoded (base64 JSON, `accepts[]`).
- LIVE (the shipped path when a funded key is present): settlement over x402 on
  **Base Sepolia** (chain 84532). The exact-scheme accept is selected, an EIP-3009
  `transferWithAuthorization` is signed, and the facilitator returns a real
  `settle.transaction` hash. The proof carries `mode="live"`, `mocked=false`,
  `rail="x402 (live)"`. Verified transactions are listed in
  `state/hackathon-state.md`.
- MOCKED (fallback only): with no wallet key configured, settlement degrades to
  the Mechanism build — no USDC moves, `tx_hash` is synthetic and every proof
  carries `mode="mocked"` + `mocked=true`. It is never presented as live.

## Config (all env-overridable; mainnet flip is a config change)

See `telegraph/config.py`: `TELEGRAPH_CHAIN_ID`, `TELEGRAPH_USDC_ADDRESS`,
`TELEGRAPH_RPC_URL`, `TELEGRAPH_PRICE_SOURCE`, `TELEGRAPH_MINER_SELECTION`,
`TELEGRAPH_NODE_URL`, `TELEGRAPH_SETTLEMENT_MODE`, etc.

Testnet defaults: Base Sepolia (chain id 84532, USDC 0x036CbD...dCF7e).

## Mainnet flip

Change env vars: `TELEGRAPH_CHAIN_ID=8453` (Base mainnet), `TELEGRAPH_USDC_ADDRESS`,
`TELEGRAPH_RPC_URL`, `TELEGRAPH_NETWORK_LABEL`, `TELEGRAPH_EXPLORER_TX_URL`,
`TELEGRAPH_SETTLEMENT_MODE=live`, `TELEGRAPH_EVM_PRIVATE_KEY=0x...`. No code change.

## Usage

```python
from telegraph.client import TelegraphClient
c = TelegraphClient()
proof = await c.buy_intelligence("Assess dengue outbreak risk in Karachi")
# proof has: mode, ranked_answer, settlement (miner, amount, tx_hash, network_label, ...)
```

`POST /telegraph/risk` surfaces the purchased `ranked_answer` as a **cited
`telegraph` driver** on the resulting card, so the buy → card chain is visible.
