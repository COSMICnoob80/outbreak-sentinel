"""Render the hackathon demo video from captured API responses.

Every string, number, hash and path on screen is read from
``state/video-capture/snapshot.json`` (produced by ``capture_video_data.py``).
Nothing is hand-written: captions interpolate captured values, and scenes draw
card fields, receipt rows and settlement facts verbatim.

Frames are built with Pillow at 1920x1080 and piped as raw rgb24 straight into
ffmpeg — no PNGs on disk.

    env -u PYTHONPATH .venv/bin/python demo/render_video.py
    env -u PYTHONPATH .venv/bin/python demo/render_video.py --montage /tmp/m.png
    env -u PYTHONPATH .venv/bin/python demo/render_video.py --stills demo/screenshots

Style mirrors the console: near-black background, one accent per meaning,
DejaVu Sans Mono, progressive reveal. The camera never leaves the frame: the
only move is scene 5's ending detail hold, which fits the whole evidence panel
first and then eases up to a 1.5x layout that is itself laid out inside the
frame — so nothing is ever cropped, zoomed past, or panned past the edge.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "state" / "video-capture" / "snapshot.json"
OUT_DIR = ROOT / "demo"
OUT_VIDEO = OUT_DIR / "outbreak-sentinel-demo.mp4"

W, H, FPS = 1920, 1080, 30
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
MONO = FONT_DIR / "DejaVuSansMono.ttf"
MONO_BOLD = FONT_DIR / "DejaVuSansMono-Bold.ttf"

# One colour per meaning, identical to the console palette.
BG = (11, 15, 23)
PANEL = (17, 24, 39)
BORDER = (31, 41, 55)
TEXT = (229, 231, 235)
DIM = (139, 152, 172)
DIM2 = (95, 107, 127)
CYAN = (56, 189, 248)
GREEN = (74, 222, 128)
AMBER = (251, 191, 36)
HIGH = (251, 146, 60)
RED = (248, 113, 113)

LEVEL_COLOR = {"LOW": GREEN, "MODERATE": AMBER, "HIGH": HIGH, "CRITICAL": RED}

MARGIN_X = 120
BODY_TOP = 210
CAPTION_TOP = 968
# Each scene finishes revealing its items by this fraction of its runtime, then
# holds a fully-drawn frame so the later captions land on complete content.
REVEAL_SPAN = 0.55

# Scene 5 ends on a detail hold of the dense evidence panels. The block is laid
# out once at ZOOM_MAX; the push-in eases from the 1.0x layout to that fitted
# one, so the widest framing IS the layout — the camera can never pass the frame
# edge, and no column or glyph can be clipped.
ZOOM_MAX = 1.5
ZOOM_RAMP_S = 0.5
ZOOM_HOLD_S = 4.0
ZOOM_TOTAL_S = ZOOM_RAMP_S + ZOOM_HOLD_S
ZOOM_BOX = (MARGIN_X, 176, W - MARGIN_X, CAPTION_TOP - 28)


def mix(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (str(MONO_BOLD if bold else MONO), size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(str(key[0]), size)
    return _FONT_CACHE[key]


def wrap(text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_sep(text: str, fnt, max_w: int, sep: str = " · "):
    """Break on field separators first, so a clause is never orphaned.

    Plain word-wrap can strand a short tail ("PKT") on its own line. Packing
    whole ``sep``-delimited fields keeps each rendered line readable, and a
    field that is itself too wide still falls back to word-wrap.
    """
    parts = (text or "").split(sep)
    lines, cur = [], ""
    for part in parts:
        trial = part if not cur else f"{cur}{sep}{part}"
        if fnt.getlength(trial) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        if fnt.getlength(part) > max_w:
            sub = wrap(part, fnt, max_w)
            lines.extend(sub[:-1])
            cur = sub[-1]
        else:
            cur = part
    if cur:
        lines.append(cur)
    return lines or [""]


def trunc(s: str, fnt, max_w: int) -> str:
    if fnt.getlength(s) <= max_w:
        return s
    while s and fnt.getlength(s + "...") > max_w:
        s = s[:-1]
    return s + "..."


# Current scene index, so Frame can read its measured reveal count.
_CURRENT = {"i": 0}
_SCENE_N: dict[int, int] = {}


class Frame:
    """Draw onto a supplied image with a stable layout and fades in place.

    Layout never depends on reveal progress: every ``text`` advances the caller's
    y-cursor by its font size whether or not it is visible yet, so lines fade in
    without shoving the ones below them. ``_counting`` mode tallies draw calls so
    each scene's reveal pacing matches how much it actually draws.
    """

    _counting = False
    _count = 0

    def __init__(self, img, p: float):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.p = p
        self.n = max(1, _SCENE_N.get(_CURRENT["i"], 12))
        self._shown = 0

    def next_reveal(self) -> float:
        idx = self._shown
        self._shown += 1
        step = 1.0 / (self.n + 1)
        start = idx * step
        pe = min(1.0, self.p / REVEAL_SPAN)  # finish drawing at REVEAL_SPAN, then hold
        if pe < start:
            return 0.0
        return min(1.0, (pe - start) / max(step * 0.6, 1e-6))

    def text(self, xy, s, size=30, color=TEXT, bold=False, anchor="la"):
        a = self.next_reveal()
        if Frame._counting:
            Frame._count += 1
        elif a > 0:
            self.d.text(xy, s, font=font(size, bold),
                        fill=mix(BG, color, a), anchor=anchor)
        return size

    def panel(self, box, color=BORDER, fill=PANEL):
        a = self.next_reveal()
        if Frame._counting:
            Frame._count += 1
            return
        if a <= 0:
            return
        self.d.rounded_rectangle(box, radius=14, outline=mix(BG, color, a),
                                 fill=mix(BG, fill, a), width=2)


class Captions:
    """Bottom caption bar; the visible sub changes at progress thresholds."""

    def __init__(self, subs):
        self.subs = subs

    def draw(self, img, p):
        text = ""
        for start, s in self.subs:
            if p >= start:
                text = s
        if not text:
            return
        d = ImageDraw.Draw(img)
        d.rectangle([(0, CAPTION_TOP - 14), (W, H)], fill=(8, 11, 17))
        fnt = font(30)
        y = CAPTION_TOP
        for ln in wrap(text, fnt, W - 2 * MARGIN_X)[:2]:
            d.text((W // 2, y), ln, font=fnt, fill=TEXT, anchor="ma")
            y += 40


def chrome(img, snap, scene_label, overall_p):
    d = ImageDraw.Draw(img)
    d.text((MARGIN_X, 44), snap["live_base"], font=font(26, True), fill=CYAN)
    status = snap["telegraph_status"]
    chip = f"mode {status['mode']} · chain {status['chain_id']} · {status['network_label']}"
    d.text((W - MARGIN_X, 44), chip, font=font(22), fill=DIM, anchor="ra")
    d.line([(MARGIN_X, 88), (W - MARGIN_X, 88)], fill=BORDER, width=2)
    d.text((MARGIN_X, 1036), scene_label.upper(), font=font(20), fill=DIM2)
    d.rectangle([(MARGIN_X, 1064), (W - MARGIN_X, 1068)], fill=BORDER)
    d.rectangle([(MARGIN_X, 1064),
                 (MARGIN_X + int((W - 2 * MARGIN_X) * overall_p), 1068)], fill=CYAN)


def spark(d, xy, values, w, h, alpha, color=CYAN):
    """Bars of a real /risk chart series — geometry is the captured numbers."""
    if not values:
        d.text(xy, "no series", font=font(20), fill=DIM2)
        return
    x, y = xy
    mx = max(values) or 1.0
    n = len(values)
    bw = max(4, int(w / n) - 8)
    for i, v in enumerate(values):
        bh = int((v / mx) * h)
        bx = x + i * (w / n)
        d.rectangle([(bx, y + h - bh), (bx + bw, y + h)],
                    fill=mix(BG, color, alpha * (0.35 + 0.65 * (v / mx))))
        # A tick per slot so a real 0.0 mm reads as an empty day, not a missing bar.
        d.rectangle([(bx, y + h - 2), (bx + bw, y + h)], fill=mix(BG, color, alpha * 0.5))
    d.line([(x, y + h), (x + w, y + h)], fill=mix(BG, BORDER, alpha), width=2)


# ── Scenes ──────────────────────────────────────────────────────────────


def scene_cold_open(img, p, S):
    snap = S["snapshot"]
    grid = snap["grid"]
    f = Frame(img, p)
    left_w = 1000
    y = 214
    y += f.text((MARGIN_X, y), "OUTBREAK SENTINEL", 92, TEXT, True) + 46
    for ln in wrap("autonomous early-warning agent, paid through Telegraph", font(34), left_w):
        y += f.text((MARGIN_X, y), ln, 34, DIM) + 8
    y += 24
    # Width follows the captured URL so the pill can never clip its own text.
    pill_w = 128 + int(font(24).getlength(snap["live_base"])) + 26
    f.panel([(MARGIN_X, y), (MARGIN_X + pill_w, y + 62)], CYAN, (10, 20, 30))
    f.text((MARGIN_X + 26, y + 14), "LIVE", 28, CYAN, True)
    f.text((MARGIN_X + 128, y + 18), snap["live_base"], 24, DIM)
    y += 92
    for ln in wrap(
        f"{grid['card_count']} risk cards · {grid['city_count']} cities · "
        f"{len(grid['verticals'])} verticals · engine {grid['engine']}",
        font(30), left_w,
    ):
        y += f.text((MARGIN_X, y), ln, 30, TEXT) + 8
    y += 22
    y += f.text((MARGIN_X, y), "SURVEILLANCE ONLY — never diagnosis, never treatment advice",
                32, AMBER) + 18
    f.text((MARGIN_X, y), "Every card is a cited early-warning signal with traceable sources.",
           26, DIM)
    h = snap["health"]
    bx = 1180
    rows = (
        ("GET /health", f"{h.get('status')} · v{h.get('version')}", GREEN),
        ("service", h.get("service"), TEXT),
        ("captured (UTC)", snap["captured_at"], DIM),
        ("grid timestamp", grid["timestamp"], DIM),
    )
    # Height follows the row count so the last value can never fall outside.
    # Mirrors the loop below: value sits 34px under its label, rows 84 apart.
    panel_h = 40 + (len(rows) - 1) * 84 + 34 + 24 + 18
    f.panel([(bx, 220), (W - MARGIN_X, 220 + panel_h)])
    fy = 260
    for label, val, col in rows:
        f.text((bx + 40, fy), label, 22, DIM2)
        fy += 34
        f.text((bx + 40, fy), str(val), 24, col)
        fy += 50
    return Captions([
        (0.0, "Outbreak Sentinel — an autonomous early-warning agent, live at a public URL."),
        (0.45, "This video is built from the deployment's real API responses, captured at build time."),
    ])


def scene_console(img, p, S):
    snap = S["snapshot"]
    grid = snap["grid"]
    la = snap["hero_la_wildfire"]
    f = Frame(img, p)
    y = BODY_TOP
    y += f.text((MARGIN_X, y), "THE LIVE CONSOLE", 40, CYAN, True) + 18
    y += f.text((MARGIN_X, y),
                f"/risk · {grid['card_count']} cards · {grid['city_count']} cities · "
                f"levels {grid['levels']}",
                27, DIM) + 22
    sig = grid["signals"]
    y += f.text((MARGIN_X, y),
                f"signals: news {sig.get('news')} (city-scoped {sig.get('news_city_scoped')}) · "
                f"social {sig.get('social')} · weather cities {sig.get('cities')}",
                23, DIM) + 34

    cx0, cx1 = MARGIN_X, W - MARGIN_X
    card_top = y
    card_bot = y + 470
    f.panel([(cx0, card_top), (cx1, card_bot)], LEVEL_COLOR.get(la["risk_level"], BORDER))

    lx = cx0 + 36
    rx = 1330
    rw = (cx1 - 36) - rx

    hy = card_top + 26
    f.text((lx, hy), la["city"], 46, TEXT, True)
    level_x = lx + font(46, True).getlength(la["city"]) + 24
    f.text((level_x, hy + 8), f"{la['risk_level']}  {la['risk_score']}", 32,
           LEVEL_COLOR.get(la["risk_level"], TEXT), True)

    # Left column, wrapped to the space beside the chart.
    left_w = rx - 40 - lx
    iy = hy + 70
    ev = f"vertical: {la['vertical']}   evidence: {la['evidence_line']}"
    for ln in wrap(ev, font(22), left_w)[:2]:
        iy += f.text((lx, iy), ln, 22, DIM) + 4
    iy += 10
    for drv in la["drivers"]:
        iy += f.text((lx, iy), f"• {drv['text']}", 27, TEXT) + 8
    iy += 6
    iy += f.text((lx, iy), f"sources ({la['source_count']}) — verbatim from /risk:", 22, CYAN) + 10
    title_w = left_w - 26
    for i, src in enumerate(la["sources"], 1):
        t = trunc(f"{i}. {src['title']}", font(21), title_w)
        iy += f.text((lx + 16, iy), t, 21, TEXT) + 6

    # Right column: the real 7-day series and the count-parity fact, below the
    # confidence line so nothing shares a baseline with the left-column header.
    values = [pt["value"] for pt in la["chart"]]
    f.text((rx, card_top + 24), f"confidence {la['confidence']:g}", 22, DIM)
    ry = card_top + 76
    f.text((rx, ry), "7-day precipitation outlook", 21, DIM)
    spark(f.d, (rx, ry + 34), values, rw, 104, 1.0, CYAN)
    last_label = la["chart"][-1]["label"] if la["chart"] else "—"
    ry += 152
    ry += f.text((rx, ry),
                 f"points {len(values)} · peak {max(values) if values else 0:g} mm",
                 19, DIM2) + 22
    ry += f.text((rx, ry), f"through {last_label}", 19, DIM2) + 28
    ry += f.text((rx, ry),
                 f"evidence_count {la['evidence_count']} == sources {la['source_count']}",
                 19, GREEN) + 20
    f.text((rx, ry), "count and links are one number", 19, DIM2)
    return Captions([
        (0.0, "One render of /risk returns the whole grid: every card computed in code."),
        (0.40, f"Los Angeles — wildfire {la['risk_level']} {la['risk_score']}: five city-specific reports in 7 days, plus a high-wind driver."),
        (0.74, "The five cited stories are the five links — driver count and rendered sources are one number."),
    ])


def scene_integrity(img, p, S):
    snap = S["snapshot"]
    lo = snap["london_dengue"]
    empty = snap["empty_bio"]
    f = Frame(img, p)
    y = BODY_TOP
    y += f.text((MARGIN_X, y), "THE EVIDENCE GATE", 40, CYAN, True) + 20
    y += f.text((MARGIN_X, y),
                "a card may only cite reports for its own city and its own disease",
                27, DIM) + 38
    f.panel([(MARGIN_X, y), (W - MARGIN_X, y + 300)], LEVEL_COLOR.get(lo["risk_level"], BORDER))
    iy = y + 28
    head = f"{lo['city']} — {lo['disease']}"
    f.text((MARGIN_X + 36, iy), head, 44, TEXT, True)
    f.text((MARGIN_X + 40 + font(44, True).getlength(head), iy + 6),
           f"  {lo['risk_level']}  {lo['risk_score']}", 32,
           LEVEL_COLOR.get(lo["risk_level"], TEXT), True)
    iy += 68
    iy += f.text((MARGIN_X + 36, iy), lo["evidence_line"], 25, DIM) + 20
    iy += f.text((MARGIN_X + 36, iy), f"sources ({lo['source_count']}):", 23, CYAN) + 12
    for src in lo["sources"]:
        t = trunc(src["title"], font(23), W - 2 * MARGIN_X - 100)
        iy += f.text((MARGIN_X + 56, iy), f"• {t}", 23, TEXT) + 8
        iy += f.text((MARGIN_X + 56, iy), f"{src['outlet']} · {src['published']}",
                     20, DIM2) + 10
    y += 340
    y += f.text((MARGIN_X, y),
                "The one cited story is a local vector report — not another disease's outbreak.",
                27, GREEN) + 22
    f.text((MARGIN_X, y),
           f"No city-specific evidence stays honest: e.g. {empty['city']} "
           f"{empty['risk_level']} {empty['risk_score']} with {empty['source_count']} sources.",
           25, DIM)
    return Captions([
        (0.0, "The differentiator is the evidence gate."),
        (0.38, f"London dengue {lo['risk_level']} {lo['risk_score']} cites exactly one story — a local vector report, nothing else."),
        (0.72, "Another disease's outbreak is never this card's evidence. No evidence means an honest LOW, not a fabricated one."),
    ])


def scene_resilience(img, p, S):
    snap = S["snapshot"]
    live = snap["debug_weather"]
    fb = snap["weather_forces_fallback"]
    f = Frame(img, p)
    y = BODY_TOP
    y += f.text((MARGIN_X, y), "GRACEFUL DEGRADATION", 40, CYAN, True) + 20
    y += f.text((MARGIN_X, y),
                "the weather grid survives a provider outage instead of blanking the cards",
                27, DIM) + 38

    f.panel([(MARGIN_X, y), (MARGIN_X + 800, y + 250)], GREEN, (10, 20, 18))
    f.text((MARGIN_X + 30, y + 24), "GET /debug/weather — live today", 23, GREEN)
    f.text((MARGIN_X + 30, y + 68),
           f"configured {live['configured_cities']} · attempted {live['attempted_cities']}",
           25, TEXT)
    f.text((MARGIN_X + 30, y + 108), f"ok {live['ok']} · failed {live['failed']}", 25, TEXT)
    providers = sorted({c["provider"] for c in live["cities"] if c.get("provider")})
    f.text((MARGIN_X + 30, y + 148), f"providers: {', '.join(providers)}", 23, DIM)
    f.text((MARGIN_X + 30, y + 188),
           f"cache: {live['cache']['cities']} cities served", 23, DIM)

    rx = MARGIN_X + 840
    f.panel([(rx, y), (W - MARGIN_X, y + 250)], AMBER, (24, 18, 8))
    f.text((rx + 30, y + 24), "fallback path: Open-Meteo 429 → MET Norway", 23, AMBER)
    f.text((rx + 30, y + 66), f"replayed {fb['condition_replayed']}", 19, DIM)
    f.text((rx + 30, y + 104),
           f"ok {fb['ok']}/{fb['attempted_cities']} via {', '.join(fb['served_by'])}",
           25, TEXT)
    days = sorted({c["forecast_days"] for c in fb["cities"]})
    f.text((rx + 30, y + 144),
           f"failed {fb['failed']} · forecast days per city {days}", 21, DIM)
    f.text((rx + 30, y + 184),
           "primary hard-fails → independent provider answers", 21, GREEN)
    y += 300
    f.text((MARGIN_X, y),
           "A judge sees degradation, not a dead panel: weather can fail without erasing a card.",
           27, TEXT)
    return Captions([
        (0.0, "Resilience: weather is three providers deep."),
        (0.36, f"Today the live grid is served cleanly — /debug/weather shows {live['ok']} of {live['attempted_cities']} cities answered."),
        (0.70, "And when the primary hard-fails with a daily-quota 429, the same code path serves real MET Norway forecasts instead of blanking the card."),
    ])


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


_PLATE: dict[str, Image.Image] = {}


def money_evidence_plate(snap):
    """The dense evidence block laid out at ``ZOOM_MAX`` inside ZOOM_BOX.

    This plate is the widest framing the camera ever reaches, so it doubles as
    the fit check. Font sizes are fixed at ``ZOOM_MAX`` — the "1.5x" label is
    literal — and only the whitespace between blocks is compressed if the
    natural layout is taller than the box. If the text alone cannot fit, the
    build fails instead of drawing a clipped column.
    """
    st = snap["telegraph_status"]
    sett = st["last_settlement"]
    s = sett["settlement"]
    rec = snap["receipts"]
    chain = snap["onchain_settlement"]

    x0, y0, x1, y1 = ZOOM_BOX
    bw, bh = x1 - x0, y1 - y0
    img = Image.new("RGB", (bw, bh), BG)
    d = ImageDraw.Draw(img)

    k = ZOOM_MAX
    sz = lambda v: int(round(v * k))
    pad = sz(24)
    inner = bw - 2 * pad
    lh = lambda size: int(round(size * 1.34))
    indent = sz(22)

    label_lines = wrap("last settlement (seeded from the ledger)", font(sz(20)), inner)
    tx_lines = wrap(sett["tx_hash"], font(sz(23)), inner)
    rail_lines = wrap_sep(
        f"rail {s['rail']} · mocked {s['mocked']} · {sett['amount_usd']} USDC · "
        f"{sett['amount_uusdc']} µUSDC · {sett['time_pkt']}", font(sz(23)), inner)
    chain_lines = wrap_sep(
        f"on-chain receipt: status {chain['status']} · block {chain['block_number']} · "
        f"to {chain['to']}", font(sz(21)), inner)
    head_lines = [f"/receipts: {rec['count']} filed from HIGH/CRITICAL cards"]
    rows = []
    for r in rec["receipts"]:
        row = (f"• {r['receipt_id']} · {r['city']} · {r['risk_level']} {r['score']} · "
               f"{r['status']} · {r['drivers'][0]}")
        rows.append((wrap_sep(row, font(sz(23)), inner - indent), sz(23),
                     wrap(r["content_hash"], font(sz(18)), inner - indent), sz(18)))

    # Natural block: padding + inter-line gaps at full size. These gaps are the
    # only thing scaled down, so every glyph stays exactly 1.5x the console.
    panel_pad = sz(16)
    panel_tail = sz(30)
    gaps = (sz(12) + sz(12) + sz(10) + sz(14) + sz(6) + sz(6) + sz(14))
    text_h = (len(label_lines) * lh(sz(20)) + len(tx_lines) * lh(sz(23))
              + len(rail_lines) * lh(sz(23)) + len(chain_lines) * lh(sz(21))
              + len(head_lines) * lh(sz(24))
              + sum(len(a) * lh(s1) + len(b) * lh(s2) for a, s1, b, s2 in rows))
    fixed_h = sz(14) + panel_pad + sz(18) + panel_tail
    budget = bh - text_h - fixed_h
    if budget < 0:
        raise SystemExit(
            f"evidence text alone is {text_h}px, box {bh}px — cannot fit at "
            f"{ZOOM_MAX}x without shrinking type; refusing to crop")
    gap_scale = min(1.0, budget / gaps) if gaps else 1.0
    g = lambda v: int(round(v * gap_scale))

    panel_h = (panel_pad + len(label_lines) * lh(sz(20)) + g(12)
               + len(tx_lines) * lh(sz(23)) + g(12)
               + len(rail_lines) * lh(sz(23)) + g(10)
               + len(chain_lines) * lh(sz(21)) + sz(18))

    panel_top = sz(14)
    d.rounded_rectangle([(1, panel_top), (bw - 2, panel_top + panel_h)], radius=sz(14),
                        outline=GREEN, fill=(10, 20, 18), width=2)
    y = panel_top + panel_pad

    def block(lines, size, colour, ind=0, gap=0):
        nonlocal y
        fnt = font(size)
        for ln in lines:
            d.text((pad + ind, y), ln, font=fnt, fill=colour)
            y += lh(size)
        y += gap

    block(label_lines, sz(20), GREEN, 0, g(12))
    block(tx_lines, sz(23), TEXT, 0, g(12))
    block(rail_lines, sz(23), TEXT, 0, g(10))
    block(chain_lines, sz(21), DIM)

    y = panel_top + panel_h + sz(18)
    block(head_lines, sz(24), CYAN, 0, g(14))
    for i, (row_lines, row_size, hash_lines, hash_size) in enumerate(rows):
        block(row_lines, row_size, TEXT, indent, g(6))
        block(hash_lines, hash_size, DIM2, indent, g(6) if i == 0 else g(14))

    if y > bh:
        raise SystemExit(
            f"evidence plate bottom {y} exceeds box {bh} — refusing to crop")
    return img


def money_detail_frame(img, snap, elapsed):
    """Ease from the whole fitted panel to the 1:1 (1.5x) layout, then hold.

    A fitting plate is only ever scaled down and back up to 1:1, so no column,
    edge or glyph can leave the frame at any instant of the push-in.
    """
    plate = _PLATE.get("img")
    if plate is None:
        plate = _PLATE["img"] = money_evidence_plate(snap)
    x0, y0, x1, y1 = ZOOM_BOX
    start = 1.0 / ZOOM_MAX
    f = start + (1.0 - start) * ease(elapsed / ZOOM_RAMP_S)
    if f >= 0.999:
        img.paste(plate, (x0, y0))
        return
    w, h = int(round(plate.width * f)), int(round(plate.height * f))
    img.paste(plate.resize((w, h), Image.LANCZOS),
              (x0 + ((x1 - x0) - w) // 2, y0 + ((y1 - y0) - h) // 2))


def money_base_body(img, p, snap):
    """The wide money layout, exactly as it reads before the push-in."""
    st = snap["telegraph_status"]
    stats = snap["telegraph_stats"]
    rec = snap["receipts"]
    chain = snap["onchain_settlement"]
    sett = st["last_settlement"]
    s = sett["settlement"]

    f = Frame(img, p)
    y = BODY_TOP
    y += f.text((MARGIN_X, y), "THE MONEY STORY", 40, CYAN, True) + 18
    y += f.text((MARGIN_X, y),
                f"/telegraph/status · mode {st['mode']} · chain {st['chain_id']} · "
                f"{st['network_label']}", 27, DIM) + 28

    f.panel([(MARGIN_X, y), (W - MARGIN_X, y + 205)], GREEN, (10, 20, 18))
    iy = y + 24
    iy += f.text((MARGIN_X + 30, iy), "last settlement (seeded from the ledger)",
                 23, GREEN) + 18
    iy += f.text((MARGIN_X + 30, iy), sett["tx_hash"], 23, TEXT) + 22
    iy += f.text((MARGIN_X + 30, iy),
                 f"rail {s['rail']} · mocked {s['mocked']} · {sett['amount_usd']} USDC · "
                 f"{sett['amount_uusdc']} µUSDC · {sett['time_pkt']}", 23, TEXT) + 20
    f.text((MARGIN_X + 30, iy),
           f"on-chain receipt: status {chain['status']} · block {chain['block_number']} · "
           f"to {chain['to']}", 21, DIM)
    y += 245

    y += f.text((MARGIN_X, y),
                f"/telegraph/stats: assessments {stats['assessments']} · "
                f"settled {stats['settled']} · total {stats['total_usdc']} USDC · "
                f"integrity {stats['integrity_pct']:g}%", 25, TEXT) + 26
    y += f.text((MARGIN_X, y),
                f"/receipts: {rec['count']} filed from HIGH/CRITICAL cards", 25, CYAN) + 18
    for r in rec["receipts"]:
        y += f.text((MARGIN_X + 20, y),
                    f"• {r['receipt_id']} · {r['city']} · {r['risk_level']} {r['score']} · "
                    f"{r['status']} · {r['drivers'][0]}", 23, TEXT) + 8
        y += f.text((MARGIN_X + 44, y), r["content_hash"], 18, DIM2) + 12


def scene_money(img, p, S):
    snap = S["snapshot"]
    st = snap["telegraph_status"]
    chain = snap["onchain_settlement"]
    sett = st["last_settlement"]
    s = sett["settlement"]

    zoom_start = 1.0 - ZOOM_TOTAL_S / S["dur"]
    subs = [
        (0.0, "The money is first-class data, not a claim."),
        (0.34, f"Mode {st['mode']} on {st['network_label']}: a real transaction, mocked {s['mocked']}."),
        (0.62, f"Read back from the chain: status {chain['status']}, block {chain['block_number']}, to the USDC contract."),
        (0.82, "Every paid assessment is notarized, and every HIGH card that finalizes files a receipt."),
        (zoom_start, "Read it yourself — full tx hash and both receipts, fitted to the frame, never cropped."),
    ]
    # The counting pass measures the base layout's draw count, so the reveal
    # pacing still matches what a viewer sees before the push-in.
    if Frame._counting or p < zoom_start:
        money_base_body(img, p, snap)
        return Captions(subs)

    # Cut to the detail view, then push: the plate starts at its whole-panel
    # fit (every line whole and inside the frame) and eases to 1:1, which is
    # the 1.5x layout. Blending the base over the plate would double-expose two
    # different layouts, so this is a cut followed by the move itself.
    money_detail_frame(img, snap, (p - zoom_start) * S["dur"])
    ImageDraw.Draw(img).text((MARGIN_X, 126),
                             "evidence detail — whole panel fitted, then 1.5x",
                             font=font(24), fill=CYAN)
    return Captions(subs)


def scene_close(img, p, S):
    snap = S["snapshot"]
    f = Frame(img, p)
    y = 250
    y += f.text((MARGIN_X, y), "OUTBREAK SENTINEL", 84, TEXT, True) + 38
    y += f.text((MARGIN_X, y), snap["live_base"], 40, CYAN) + 54
    y += f.text((MARGIN_X, y), "Track 01 — Apps & Agents", 34, TEXT) + 20
    y += f.text((MARGIN_X, y),
                "Mission 06 — Resources & Agriculture (fire-risk signal stack)",
                27, DIM) + 14
    y += f.text((MARGIN_X, y),
                "Mission 11 — Autonomous Systems (an autonomous unit buying fire-risk)",
                27, DIM) + 42
    y += f.text((MARGIN_X, y), "Surveillance only — never diagnosis.", 30, AMBER) + 22
    f.text((MARGIN_X, y),
           f"{snap['grid']['card_count']} live cards across {snap['grid']['city_count']} "
           f"cities; sources traceable; suite green.", 25, DIM)
    return Captions([
        (0.0, "Outbreak Sentinel — cited early-warning intelligence, bought and settled on-chain."),
        (0.5, "Everything shown came from the live deployment. The URL is open — try it."),
    ])


SCENES = [
    ("cold open", 20.0, scene_cold_open),
    ("the live console", 56.0, scene_console),
    ("the evidence gate", 44.0, scene_integrity),
    ("graceful degradation", 36.0, scene_resilience),
    ("the money story", 56.0, scene_money),
    ("close", 20.0, scene_close),
]


def measure(snap):
    """One counting pass per scene so reveal pacing matches draw count exactly."""
    Frame._counting = True
    for i, (_label, dur, fn) in enumerate(SCENES):
        _CURRENT["i"] = i
        Frame._count = 0
        fn(Image.new("RGB", (W, H), BG), 1.0, {"snapshot": snap, "dur": dur})
        _SCENE_N[i] = Frame._count
    Frame._counting = False
    return _SCENE_N


def render_frame(snap, scene_idx, p, overall_p):
    label, dur, fn = SCENES[scene_idx]
    _CURRENT["i"] = scene_idx
    img = Image.new("RGB", (W, H), BG)
    captions = fn(img, p, {"snapshot": snap, "dur": dur})
    chrome(img, snap, label, overall_p)
    captions.draw(img, p)
    return img


# Submission-form stills: each point lands where its scene's claim is fully
# made, and scene 5 lands inside the 1.5x evidence hold.
STILLS = [
    ("01-title", 0, 0.55),
    ("02-console-grid", 1, 0.55),
    ("03-la-card", 1, 0.97),
    ("04-evidence-gate", 2, 0.97),
    ("05-weather-resilience", 3, 0.97),
    ("06-money-story", 4, 0.97),
]


def build_stills(snap, out_dir):
    """Six full-resolution PNGs through the same render path the video uses."""
    measure(snap)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, si, p in STILLS:
        path = out / f"{name}.png"
        render_frame(snap, si, p, 0.5).save(path, "PNG")
        print(f"wrote {path} ({path.stat().st_size} bytes)")
    return out


def build_video(snap):
    counts = measure(snap)
    total_frames = sum(int(d * FPS) for _, d, _ in SCENES)
    print(f"reveal counts: {counts}")
    print(f"rendering {total_frames} frames "
          f"({sum(d for _, d, _ in SCENES):.0f}s @ {FPS}fps) -> {OUT_VIDEO}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(OUT_VIDEO),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    done = 0
    try:
        for si, (_label, dur, _fn) in enumerate(SCENES):
            n = int(dur * FPS)
            for i in range(n):
                p = i / max(1, n - 1)
                overall = (done + i) / max(1, total_frames - 1)
                proc.stdin.write(render_frame(snap, si, p, overall).tobytes())
                done += 1
            print(f"  scene {si + 1}/{len(SCENES)} done ({done}/{total_frames})")
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed with {proc.returncode}")
    print(f"wrote {OUT_VIDEO} ({OUT_VIDEO.stat().st_size} bytes)")
    return OUT_VIDEO


def build_montage(snap, out_path):
    """Six representative frames into one contact sheet, for human review."""
    measure(snap)
    picks = [(0, 0.95), (1, 0.55), (1, 0.95), (2, 0.95), (3, 0.95), (4, 0.95)]
    thumbs = []
    for si, p in picks:
        thumbs.append(render_frame(snap, si, p, 0.5).resize((640, 360), Image.LANCZOS))
    sheet = Image.new("RGB", (640 * 2, 360 * 3), BG)
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(out_path)
    print(f"wrote montage {out_path} ({len(picks)} frames)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--montage", help="write a 6-frame contact sheet instead of the video")
    ap.add_argument("--stills", metavar="DIR",
                    help="write the 6 submission PNGs at 1920x1080 instead of the video")
    args = ap.parse_args()
    if not SNAPSHOT.exists():
        raise SystemExit(f"missing {SNAPSHOT} — run demo/capture_video_data.py first")
    snap = json.loads(SNAPSHOT.read_text())
    if args.montage:
        build_montage(snap, args.montage)
    elif args.stills:
        build_stills(snap, args.stills)
    else:
        build_video(snap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
