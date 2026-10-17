# Deploy — Outbreak Sentinel

One-command deploy targets (free tiers). App binds `0.0.0.0` and reads `$PORT`.

## Railway

```bash
railway init --name outbreak-sentinel
railway variables set GROQ_API_KEY=<your-key> TELEGRAPH_SETTLEMENT_MODE=mock
railway up
```

Live URL printed by `railway up` (or `railway status`).

## Render

Create a Web Service from this repo (Dockerfile auto-detected), or via CLI:

```bash
# render.yaml not required; Render detects Dockerfile
# Set env vars in dashboard: GROQ_API_KEY, TELEGRAPH_SETTLEMENT_MODE
```

One-shot with Render CLI (if installed): `render deploy`.

## Fly.io

```bash
fly launch --no-deploy --name outbreak-sentinel
fly secrets set GROQ_API_KEY=<your-key> TELEGRAPH_SETTLEMENT_MODE=mock
fly deploy
```

## Health check

All targets should hit `/health` (returns `{"status":"ok",...}`). railway.json already sets `healthcheckPath: /health`.

## Notes

- `.env` is gitignored; inject secrets via platform env vars.
- Container starts with an empty ledger (`history/receipts.jsonl` excluded from image). Mount a volume if persistence is needed.
- Settlement is mocked by default. To enable live settlement set `TELEGRAPH_SETTLEMENT_MODE=live` and `TELEGRAPH_EVM_PRIVATE_KEY=<funded Base Sepolia key>` (requires USDC on Base Sepolia).