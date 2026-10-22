# Shotlist — v5 console, 60-second judge cut

Recorder (OBS or any): **1920x1080**, 60 fps, CQP 18, x264/NVENC, MKV → MP4, audio 48 kHz mono, cursor highlight on, browser zoom 110%.
Desktop: solid wallpaper **#0b0f17** (matches console bg), dock/tray hidden, Do Not Disturb on, bookmarks bar off, one 1920x1080 window.

Pre-flight: `env -u PYTHONPATH .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001`
Console: `http://127.0.0.1:8001/telegraph/dashboard` — SIMPLE mode, feed loaded before you hit record.
S1–S10 = one continuous take, no cuts. S11–S13 = B-roll inserts. S14 = proof wall.

### S1 · 0:00–0:05 · hook
- URL: console at top. Frame: header, `engine: llm` badge, testnet banner.
- Action: none; cursor parked bottom-right.
- Cap: `demo/media/01-hook.mp4`
### S2 · 0:05–0:15 · fragmented signals
- URL: same page.
- Action: hover three feed items in the left column; rest cursor on a news/weather/social chip pair.
- Cap: `demo/media/02-feed.mp4`
### S3 · 0:15–0:20 · type the ask
- URL: same page, settlement panel in view.
- Action: click query field, type slowly `dengue outbreak risk Karachi`; set city `Karachi`, disease `dengue`.
- Cap: `demo/media/03-query.mp4`
### S4 · 0:20–0:24 · buy
- URL: same page.
- Action: hover **Buy through Telegraph** (2s), click once. Hold on `Settling…`.
- Cap: `demo/media/04-buy.mp4`
### S5 · 0:24–0:30 · the wait
- URL: same page. Do not cut, do not move the cursor.
- Action: none — panel stays in frame until the chip lands (~24s real time).
- Cap: `demo/media/05-wait.mp4`
### S6 · 0:30–0:33 · LIVE SETTLEMENT PROVEN
- URL: same page.
- Action: rest cursor on the green `LIVE SETTLEMENT PROVEN` chip, then on the `SETTLED ON-CHAIN` strip `0x3825fa28…`.
- Cap: `demo/media/06-chip.mp4`
### S7 · 0:33–0:35 · explorer
- URL: click the tx link → `sepolia.basescan.org/tx/0x3825fa28…`
- Action: scroll to the confirmation row; zoom so block **48,410,853** is readable aloud.
- Cap: `demo/media/07-explorer.mp4`
### S8 · 0:35–0:42 · breadth
- URL: back to console.
- Action: scroll cards past `PAKISTAN` into `GLOBAL`; hover engine badge, a citation chip, AI summary line, card-foot sparkline.
- Cap: `demo/media/08-breadth.mp4`
### S9 · 0:42–0:50 · SIMPLE → PRO
- URL: same page, receipt panel.
- Action: click `PRO`; hold on miner, micro-units, scheme, block; click back to `SIMPLE`.
- Cap: `demo/media/09-pro.mp4`
### S10 · 0:50–0:60 · close
- URL: same page, PRO receipt strip.
- Action: nothing moves; freeze tx strip, block, receipt hash for the full 10s.
- Cap: `demo/media/10-close.mp4`
### S11 · B-roll · tests
- Terminal: `env -u PYTHONPATH .venv/bin/python -m pytest tests -q` → `3 passed`.
- Cap: `demo/media/b1-pytest.mp4`
### S12 · B-roll · commits
- Terminal: `git log --oneline -5` — frame `4fef68a` and `dce42d4` on screen.
- Cap: `demo/media/b2-gitlog.mp4`
### S13 · B-roll · second settlement
- URL: `sepolia.basescan.org/tx/0xfbfe793e…` — block **48,407,506**; hover From/To and the USDC transfer log.
- Cap: `demo/media/b3-tx2.mp4`
### S14 · Proof wall (closing card, 3–4s)
- Stack: basescan tx page (zoomed to block) · console `LIVE SETTLEMENT PROVEN` chip · engine `llm` badge + PRO strip (miner, micro-units, scheme).
- Caption: `0.01 USDC · Base Sepolia · 19.97 USDC left on 0x7b3654…` · Cap: `demo/media/14-proof-wall.mov`

## Cut list (if long)
Drop in order: S11, S12, S13. Never drop S5 (wait), S6 (chip), S7 (block), S14 (proof wall).

## Do not
- Do not fake or re-type a tx hash; every hash on screen must open a real explorer URL.
- Do not hide the testnet banner or call the chain mainnet.
- Do not speed-ramp S5 — the wait is credibility, not dead air.
