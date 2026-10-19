# Base Sepolia Funding Runbook (ETH for gas + USDC for x402 payments)

Goal: fund a brand-new test wallet with **testnet ETH** (pays transaction fees)
and **testnet USDC** (the money your agent actually pays with on x402), then
wire it into deploy/README.md's live-settlement env vars.

This runbook is written for someone who has never touched a crypto wallet.
Time: ~10 minutes. Cost: **$0 — this is test money with no real-world value.**

## Safety first — read before anything else

- **Create a fresh, throwaway wallet.** Its private key will eventually sit in
  an env var in a server config. Never put real funds in it. Ever.
- Nothing in this document touches mainnet. If a site asks you to pay real
  money for "Sepolia ETH", it is a scam — close the tab.
- The private key is like the master password to the wallet. Anyone who sees
  it can move the (worthless) funds. Don't paste it in chats, commits, or docs.
- **Never `cat` or paste the contents of `.env`** — it holds that key.

## The network you're working on

| Thing | Value |
|---|---|
| Network name | Base Sepolia (Base's testnet) |
| Chain ID | `84532` |
| RPC URL | `https://sepolia.base.org` |
| Block explorer | `https://sepolia.basescan.org` |
| Test USDC token contract | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Currency symbol | ETH (gas) / USDC, 6 decimals, so 1 USDC = 1,000,000 `amount_uusdc` |

These match the defaults in `telegraph/config.py` — do not change them per
environment; the settlement code expects exactly these.

## Step 1 — Create a fresh wallet (MetaMask, 3 minutes)

1. In your browser, install the **MetaMask** extension from
   <https://metamask.io/> (Chrome, Firefox, Edge, Brave all work). Avoid
   look-alike extension names; verify the publisher is "MetaMask".
2. Click the extension icon → **Create a new wallet**.
3. MetaMask shows a 12-word recovery phrase. Write it down somewhere private
   (paper, not a screenshot). You will not need it for this project, but it is
   the only backup of the wallet.
4. MetaMask auto-creates an account. On the home screen you'll see an address
   starting with `0x` followed by 40 hex characters (e.g. `0x1a2b...`).
   Click the address to **copy it** — you'll paste it into every faucet.

> No purchase is needed anywhere in MetaMask. Ignore any "Buy" prompts.

## Step 2 — Switch MetaMask to Base Sepolia (1 minute)

1. In MetaMask, click the network selector at the top-left (currently says
   "Ethereum Mainnet").
2. Find **Base Sepolia** in the list. If it isn't listed, click
   **Add network manually** and fill in the table above (name, RPC URL,
   chain ID `84532`, currency ETH, explorer URL).
3. Select it when done. The wallet background color/name changes.

## Step 3 — Get test ETH (gas money)

Try the faucets in this order. One success is enough — you need roughly
0.001 ETH and each drip is far more.

### Option A: QuickNode — works with a brand-new wallet, zero conditions

1. Open <https://faucet.quicknode.com/base/sepolia>.
2. Confirm the network panel says **Base** / **Sepolia** (chain ID 84532).
3. Either connect your MetaMask (click "Connect wallet") or simply paste your
   `0x...` address into the address box.
4. Complete the bot check, click **Claim / Continue**, and confirm.
5. The base drip is free — no account, no X/Twitter post, no mainnet balance
   required. Optional bonus steps exist but are **not required**. One claim
   per wallet per 12 hours.

### Option B: Coinbase Developer Platform — also gives USDC (see Step 4)

1. Go to <https://portal.cdp.coinbase.com/products/faucet>.
2. Sign in with a free **Coinbase developer account** (no bank/card needed).
3. Network: **Base Sepolia**, Asset: **ETH**, paste your `0x...` address →
   **Claim**.
4. Same screen also supports **USDC** claims — do both.
5. Rate limit: one claim per asset per 24 hours.

### Option C: Alchemy — biggest drip, but eligibility-gated

1. Open <https://www.alchemy.com/faucets/base-sepolia>.
2. Paste your `0x...` address → **Send**.
3. Fine print it checks: your wallet must hold at least **0.001 ETH on
   Ethereum *mainnet*** and have some real mainnet activity, and must not
   already be stuffed with testnet funds. A fresh wallet usually fails here —
   that's why it's Option C, not A. Reuse the address you created in Step 1;
   do **not** create another wallet.

## Step 4 — Get test USDC (the money x402 pays with)

The Circle faucet is the standard source:

1. Sign in to <https://faucet.circle.com> (quick email/GitHub sign-up).
2. From the network list choose **Base Sepolia**.
3. Paste the same wallet address and select the **USDC** asset.
4. Submit. You'll receive test USDC directly to the wallet — typically
   enough for hundreds of x402 payments (receipts here are micro-USDC:
   `amount_uusdc` values like `1000` = 0.001 USDC).
5. Circle refreshes claims on a cooldown; the Coinbase Developer faucet
   (Option B above) is a backup source. Confirm the token you received
   matches contract `0x036CbD53842c5426634e7929541eC2318f3dCF7e` — that is
   the exact address in `telegraph/config.py`.

MetaMask may show the USDC balance only after you add the token: in MetaMask,
**Tokens → Import token → paste the contract address above** (name USDC,
decimals 6).

## Step 5 — Verify the balances landed

You should now have both listed on the wallet home page.

1. Open <https://sepolia.basescan.org/address/your0xAddressHere> — replace the
   address with your own after the `/address/` path.
2. Confirm you see **ETH** and a value like `0.05...` (from a faucet).
3. Scroll to **Token Holdings** and confirm you see **USD Coin (USDC)**. If it
   says "Private Name Tag" USDC, that's still the right token when the
   contract address ends `...dCF7e`.
4. A quick sanity test: send a tiny amount (e.g. 0.0005 ETH) from your wallet
   to itself. If it goes through, the wallet can transact and pay gas — the
   exact skill settlement needs.

## Step 6 — Wire the wallet into the app

`telegraph/README.md` and `deploy/README.md` document the same live mode —
consistency check:

- `TELEGRAPH_SETTLEMENT_MODE=live`
- `TELEGRAPH_EVM_PRIVATE_KEY=0x...` (the wallet's private key)
- Optional overrides: `TELEGRAPH_RPC_URL` (default `https://sepolia.base.org`),
  `TELEGRAPH_CHAIN_ID` (default `84532`),
  `TELEGRAPH_USDC_ADDRESS` (default `0x036CbD53842c5426634e7929541eC2318f3dCF7e`),
  `TELEGRAPH_EXPLORER_TX_URL` (default
  `https://sepolia.basescan.org/tx/{tx_hash}`).

**Get the private key safely:**

1. In MetaMask, click the account menu → **Account details** →
   **Show private key** → enter your password (browser only, never in a
   screenshot or chat).
2. Copy the 64-character key. MetaMask prefixes it `0x` when you copy.

**Set it without ever printing it:**

```bash
export TELEGRAPH_SETTLEMENT_MODE=live
export TELEGRAPH_EVM_PRIVATE_KEY=0xYourKeyHere   # paste, then press Enter once
unset HISTFILE                                    # bash: don't log this command
```

Or, for platform hosts (Railway / Render / Fly), set the two variables in
their dashboard — that is what deploy/README.md's live-settlement note
describes. Locally, keep them in `.env`; the file is gitignored, and never
`cat` it or paste its contents anywhere.

## Verification checklist (all of these must be true)

- [ ] MetaMask shows the wallet on **Base Sepolia**, chain ID **84532**.
- [ ] Balance on sepolia.basescan.org shows **> 0 ETH** (gas) and **> 0 USDC**
      at contract `0x036CbD...dCF7e`.
- [ ] After a live transaction the dashboard/receipt shows a real **tx hash**;
      open
      `https://sepolia.basescan.org/tx/<that hash>` and confirm it exists with
      a "Success" status — mock mode produces `0xMOCK_PAYER_NOT_A_REAL_WALLET`
      and there is nothing to look up.
- [ ] Receipt shows `amount_uusdc` (micro-USDC); divide by 1,000,000 to see
      how many real USDC it represents — e.g. `1000` = 0.001 USDC.
- [ ] No real money: all tokens on Base Sepolia are testnet-only, worth $0.

## Troubleshooting

| Symptom | Fix |
|---|---|
| QuickNode/CDP faucet button stays grey | It's the per-wallet cooldown (12h/24h). Come back later or use another faucet above. |
| Circle faucet says "not eligible" | Ensure a Base Sepolia address was selected (not Base mainnet), and try again later; the Coinbase faucet (Step 3 Option B) also gives USDC. |
| Alchemy says you're ineligible | It needs mainnet history and a non-empty mainnet balance — stick to QuickNode for a fresh wallet. |
| Balances visible in MetaMask, not on Basescan | You added the wrong network — confirm the RPC is `https://sepolia.base.org` and Chain ID `84532`. |
| A site offers "free ETH" for a payment or asks for your seed phrase | Scam. No faucet in this runbook ever wants money, and none ever needs your 12-word phrase. |
| Live settlement says insufficient USDC | Reclaim from Circle (cooldown applies) or claim via the Coinbase faucet. `amount_uusdc` per payment is tiny, so even 1 USDC goes very far. |
| Wrong-token imported by hand | Contract address must end `...dCF7e`; anything else is a different (possibly fake) token. |
