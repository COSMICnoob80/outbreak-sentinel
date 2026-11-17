# Deploy — Outbreak Sentinel

One-command deploy targets (free tiers only). The app binds `0.0.0.0` and reads
`$PORT`.

**The documented path is the Render blueprint.** `render.yaml` at the repo root
describes the whole service — region, free plan, build command, start command,
health check — so Render fills in the form for you. You supply two secrets and
nothing else.

## Render (blueprint)

1. Go to <https://dashboard.render.com> and sign in.
2. **New** → **Blueprint**.
3. Connect GitHub if asked, then pick this repo on branch `main`.
4. Render shows the service it found in `render.yaml`. Paste the two secrets when
   it prompts:

   | Secret | Value |
   |---|---|
   | `CMDC_API_KEY` | Command Code provider key — lets the app call the language model |
   | `TELEGRAPH_EVM_PRIVATE_KEY` | Base Sepolia test wallet key — enables live settlement |

5. Click **Apply**. The first build takes a few minutes and ends with a green
   "live" dot.

Your URL is `https://outbreak-sentinel.onrender.com` (if the name is taken Render
adds a suffix; the exact URL is at the top of the service page). Every push to
`main` redeploys automatically.

Full walkthrough including the free-plan sleep caveat:
[`docs/DEPLOY-RENDER.md`](../docs/DEPLOY-RENDER.md).

## Other targets

Any container host works — the repo ships a `Dockerfile`, `Procfile` and
`docker-compose.yml`; a web service just needs the same two env vars and
`/health` as its check. The blueprint above is the path we actually verify;
`fly.toml` is not shipped, so the snippet below is the only extra target.

```bash
fly launch --no-deploy --name outbreak-sentinel
fly secrets set CMDC_API_KEY=<your-key> TELEGRAPH_SETTLEMENT_MODE=mock
fly deploy
```

## Health check

Every target should hit `/health` (returns `{"status":"ok",...}`). `render.yaml`
sets `healthCheckPath: /health`.

`/intel/llm` is the provider proof: it should return `"ok": true` and
`"provider": "commandcode"`. If it returns `"provider": null`, the `CMDC_API_KEY`
secret is missing or mistyped.

## Notes

- `.env` is gitignored; inject secrets via platform env vars. Never commit them,
  never paste them into a chat, never put them in `render.yaml`.
- `GROQ_API_KEY` is not required. It is only a fallback if you have a working key;
  Groq currently answers HTTP 403 on our account.
- Container starts with an empty ledger (`history/receipts.jsonl` excluded from the
  image). Mount a volume if persistence is needed.
- Settlement is live by default in the blueprint (`TELEGRAPH_SETTLEMENT_MODE=live`).
  Use `mock` to skip on-chain settlement; live mode requires
  `TELEGRAPH_EVM_PRIVATE_KEY` with USDC on Base Sepolia.
