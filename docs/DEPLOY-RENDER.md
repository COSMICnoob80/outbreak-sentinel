# Deploying Outbreak Sentinel on Render (the short version)

This repo contains a file called `render.yaml`. Render reads it and fills in the whole
service form for you — region, free plan, build command, start command, health check.
You only supply **two secrets**, and you type them into Render's website. Nothing secret is
stored in this repo.

## The two secrets

| Secret name | Where you copy the value from |
|---|---|
| `CMDC_API_KEY` | Open `~/.commandcode/auth.json` on your own machine and copy the text after `"apiKey":` (just the value, without the quotes). This is what lets the app call the language model (`tencent/hy4-flash`, set by `LLM_MODEL`). |
| `TELEGRAPH_EVM_PRIVATE_KEY` | Open the `.env` file in this project folder and copy the value after `TELEGRAPH_EVM_PRIVATE_KEY=`. This is the Base Sepolia test wallet key. |

Paste each one into Render's dashboard when it asks (or under the service's
**Environment** tab afterwards). **Never commit these values to git, never paste them into a
chat, and never put them in `render.yaml`.** If a secret is wrong or missing the app still
starts — it just runs without the model, or without live settlement.

Nothing else is needed. `GROQ_API_KEY` is deliberately not configured.

## The click path

1. Go to <https://dashboard.render.com> and sign in.
2. Click **New** → **Blueprint**.
3. Connect your GitHub account if asked, then pick the repo `COSMICnoob80/outbreak-sentinel`
   on branch `main`.
4. Render shows the service it found in `render.yaml`. Paste the two secret values when it
   prompts for them.
5. Click **Apply**. The first build takes a few minutes and ends with a green "live" dot.

Your URL is `https://outbreak-sentinel.onrender.com` — if Render says the name is taken it
adds a suffix, and the exact URL is shown at the top of the service page.

## Free plan caveat (be patient, nothing is broken)

- The free instance **sleeps after about 15 minutes with no visitors**. The next request has
  to wake it: expect **about 50 seconds** before anything appears.
- The **first page load also runs one real model call**, which can add up to about **30
  seconds**. So the first visit after a sleep can take roughly a minute and a half.
- After that it is fast: results are **cached for five minutes**, so reloads and repeat
  checks return immediately.

## Did it work? (two checks)

```bash
curl https://outbreak-sentinel.onrender.com/health
curl https://outbreak-sentinel.onrender.com/intel/llm
```

- `/health` should return `{"status":"ok", ...}` — the service is up.
- `/intel/llm` should show `"ok": true` and a provider name such as
  `"provider": "commandcode"`.
- If `/intel/llm` shows `"provider": null` (or `"ok": false`), the **`CMDC_API_KEY` secret is
  missing or mistyped** — fix it under **Environment** and redeploy.

Every later push to `main` redeploys automatically.
